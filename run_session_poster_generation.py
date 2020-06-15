import pandas as pd
import os
import subprocess
import numpy as np
from natsort import natsorted

DIR_PATH = os.path.dirname(os.path.abspath(__file__))

AFFILIATION_SEPARATOR = ", "


def is_not_an_empty_cell(cell):
    if str(cell) == 'nan' or str(cell) == '0' or str(cell) == '':
        return False
    else:
        return True


def is_empty_cell(cell):
    return str(cell) == 'nan' or str(cell) == '0' or str(cell) == '' or str(cell) == 'NaN'


def main():
    print("Starting session poster generation...")
    original_file_path = os.path.join(DIR_PATH, 'technical_program.csv')
    data = pd.read_csv(original_file_path, sep=";")
    sessionIDs = data.SessionID.unique()
    sessionIDs_of_interest = [sessionID for sessionID in sessionIDs if (isinstance(sessionID, str) and ("-O-" in sessionID or "-P-" in sessionID or "-SS-" in sessionID))]

    for sessionID in sessionIDs_of_interest:
        # select data for each session
        session_data = data.loc[data['SessionID'] == sessionID]

        # sort by 'Category', 'time', 'paper_code'
        session_data['paper_code'] = session_data['paper_code'].apply(lambda x: "" if is_empty_cell(x) else x)
        session_data['paper_code'] = pd.Categorical(session_data['paper_code'], ordered=True, categories=natsorted(session_data['paper_code'].unique()))

        session_data['Category'] = pd.Categorical(session_data['Category'], ordered=True, categories=['Session Title', 'Survey Talk', 'Oral', 'Poster'])
        session_data = session_data.sort_values(['Category', 'time', 'paper_code'])

        # save authors and affiliations as tex strings
        session_data.insert(13, "authors_tex", [''] * len(session_data), True)
        session_data.insert(14, "affiliations_tex", [''] * len(session_data), True)

        session_program_folder = os.path.join(DIR_PATH, 'session_program_files')
        if not os.path.exists(session_program_folder):
            os.makedirs(session_program_folder)

        for index, row in session_data.iterrows():
            if row['Category'] == 'Session Title':
                authors_first_name_format = 'chair_{}_first_name'
                authors_last_name_format = 'chair_{}_last_name'
                authors_affiliation_format = 'chair_{}_affiliation'
                max_authors = 2
            else:
                authors_first_name_format = '{}: First Name'
                authors_last_name_format = '{}: Last Name'
                authors_affiliation_format = '{}: Affiliation'
                max_authors = 5
            authors = []
            author_markers = []
            affiliations = []
            affiliation_markers = []
            affiliation_marker_dict = {}
            affiliation_marker_nr = 1
            for authors_idx in range(1, max_authors+1):
                author_first_name_key = authors_first_name_format.format(str(authors_idx))
                author_last_name_key = authors_last_name_format.format(str(authors_idx))
                author_affiliation_key = authors_affiliation_format.format(str(authors_idx))

                if is_not_an_empty_cell(row[author_first_name_key]) or is_not_an_empty_cell(row[author_last_name_key]):
                    author = ''
                    if is_not_an_empty_cell(row[author_first_name_key]):
                        author += row[author_first_name_key]
                    if is_not_an_empty_cell(row[author_first_name_key]) and is_not_an_empty_cell(row[author_last_name_key]):
                        author += ' '
                    if is_not_an_empty_cell(row[author_last_name_key]):
                        author += ' ' + row[author_last_name_key]
                    author = author.replace('\n', ' ')
                    author = author.replace(';', ' ')
                    author = author.strip()
                    authors.append(author)

                    if is_not_an_empty_cell(row[author_affiliation_key]):
                        affiliation = row[author_affiliation_key]
                        affiliation = affiliation.replace('\n', ' ')
                        affiliation = affiliation.replace(';', ' ')
                        affiliation = affiliation.strip()
                        if affiliation not in affiliation_marker_dict.keys():
                            affiliation_marker_dict[affiliation] = str(affiliation_marker_nr)
                            affiliation_marker_nr += 1
                            affiliations.append(affiliation)
                            affiliation_markers.append('$^{' + affiliation_marker_dict[affiliation] + '}$')

                        author_markers.append('$^{' + affiliation_marker_dict[affiliation] + '}$')
                    else:
                        author_markers.append('')

            if len(authors) == 1:
                authors_tex_str = ", ".join(authors)
                affiliations_tex_str = AFFILIATION_SEPARATOR.join(affiliations)
            elif len(affiliation_marker_dict.keys()) == 1:
                authors_tex_str = ", ".join(authors)
                affiliations_tex_str = affiliations[0]
            else:
                authors_tex_str = ', '.join([authors[i] + author_markers[i] for i in range(len(authors))])
                affiliations_tex_str = AFFILIATION_SEPARATOR.join([affiliations[i] + affiliation_markers[i] for i in range(len(affiliations))])

            row['authors_tex'] = authors_tex_str
            row['affiliations_tex'] = affiliations_tex_str

            # remove special characters
            title = row['Title']
            title = title.replace('\n', ' ')
            title = title.replace(';', ' ')
            row['Title'] = title

            session_data.loc[index] = row


        # save session file
        session_file_path = os.path.join(DIR_PATH, 'session_program_files', 'program_' + sessionID + '.csv')
        session_data.to_csv(session_file_path, sep=';')

        # generate pdf with session data as input
        latex_command = ['pdflatex', '-interaction=nonstopmode', '-output-directory=session_program_files', '-jobname='+ sessionID, '\def\SessionFile{program_'+sessionID+'.csv} \input{session_template.tex}']
        output = subprocess.Popen(latex_command, stdout=subprocess.PIPE).communicate()[0]
        print(output)
        # run twice to ensure the images are displayed
        output = subprocess.Popen(latex_command, stdout=subprocess.PIPE).communicate()[0]
        print(output)
        # cleanup files
        rm_path = os.path.join(DIR_PATH, 'session_program_files', sessionID + '.log')
        output = subprocess.Popen(['rm', rm_path], stdout=subprocess.PIPE).communicate()[0]
        print(output)
        rm_path = os.path.join(DIR_PATH, 'session_program_files', sessionID + '.aux')
        output = subprocess.Popen(['rm', rm_path], stdout=subprocess.PIPE).communicate()[0]
        print(output)
        rm_path = session_file_path
        output = subprocess.Popen(['rm', rm_path], stdout=subprocess.PIPE).communicate()[0]
        print(output)

        print('Finished sessionID: ' + sessionID)

    # pdf unite all files in sort order
    rooms_for_sessions_dict = {}
    for sessionID in sessionIDs_of_interest:
        session_title = data[(data['SessionID'] == sessionID) & (data['Category'] == 'Session Title')]
        session_room = session_title.iloc[0]['room']
        if session_room in rooms_for_sessions_dict.keys():
            rooms_for_sessions_dict[session_room].append(sessionID)
        else:
            rooms_for_sessions_dict[session_room] = [sessionID]

    for room in rooms_for_sessions_dict.keys():
        # create directory for room if it doesn't exist
        room_dir = os.path.join(DIR_PATH, 'session_program_files', room.replace('/', '-'))
        if not os.path.exists(room_dir):
            os.makedirs(room_dir)


        pdfunite_command = ['pdfunite']
        sessions_in_room = rooms_for_sessions_dict[room]
        sessions_in_room_data = data[data['SessionID'].isin(sessions_in_room) & (data['Category'] == 'Session Title')]
        sessions_in_room_data = sessions_in_room_data.sort_values(['date', 'time', 'SessionID'])

        sessionID_file_nr = 1
        for sessionID in sessions_in_room_data['SessionID']:
            # mv session-pdf to room directory
            session_pdf_file = os.path.join(DIR_PATH, 'session_program_files', sessionID + '.pdf')
            session_pdf_file_in_room_folder = os.path.join(room_dir, '{:02d}_'.format(sessionID_file_nr) + sessionID + '.pdf')
            output = subprocess.Popen(['mv', session_pdf_file, session_pdf_file_in_room_folder], stdout=subprocess.PIPE).communicate()[0]
            sessionID_file_nr += 1

            # pdfunite all session posters in room
            pdfunite_command.append(session_pdf_file_in_room_folder)
        pdfunite_command.append(os.path.join(DIR_PATH, 'session_program_files', room.replace('/', '-') + '.pdf'))
        output = subprocess.Popen(pdfunite_command, stdout=subprocess.PIPE).communicate()[0]
        print(output)
    print("DONE.")


main()
