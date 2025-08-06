#event times are logged with reference to SPACE key press, not window popup
#pause function is just an emergency measure, not supposed to be used by participants

from psychopy import visual, core, event, gui, parallel
import pandas as pd
import csv
import os
import traceback
from datetime import timedelta, datetime

# Set the parallel port address
parallel.setPortAddress(0x3FE8)  # Replace with your actual parallel port address
# Clear any previous settings or data on the parallel port
parallel.setData(0)

#Basic Code to send a trigger
# Send trigger value, e.g., 5
parallel.setData(255)
# Short pulse duration using core.wait
core.wait(0.01)  # Adjust the delay if needed
# Reset the parallel port (clear the trigger)
parallel.setData(0)

# ---------- Get Participant Info ----------
# Create a dialog box to get participant ID; exit if cancelled
participant_info = {'Participant ID': ''}
dlg = gui.DlgFromDict(dictionary=participant_info, title='Participant Info')
if not dlg.OK:
    core.quit()

# Use participant ID to name the data files
participant_id = participant_info['Participant ID']
data_filename = f"{participant_id}_data.csv"
word_log_filename = f"{participant_id}_word_log.csv"

# ---------- Load Stimuli ----------
stimuli_df = pd.read_csv('randomized_list_1.csv')

# ---------- Create Window ----------
win = visual.Window(fullscr=False, color='white', units='pix')

# ---------- Show Instructions ----------
instruction_text = (
    "Καλωσορίσατε!\n\n" #Welcome!
    "Σε αυτό το πείραμα θα εμφανίζονται προτάσεις λέξη-λέξη.\n\n" #In this experiments sentences will be presented word by word
    "Πρέπει απλώς να τις διαβάζετε από μέσα σας.\n\n" #You only have to read them to yourself
    "Κάποιες φορές θα εμφανίζονται ερωτήσεις. Απαντήστε πατώντας 'N' για Ναι ή 'O' για Όχι.\n\n" #Occasionally there will be questions. Answer by pressing N for yes and O for no -- not sure if this is ideal
    "Πατήστε SPACE για να ξεκινήσετε." #Press SPACE to start
)
instruction = visual.TextStim(win, text=instruction_text, color='black', height=30, wrapWidth=800)
instruction.draw()
win.flip()

# Wait for SPACE key and record time when pressed
start_press_time = core.getTime()
event.waitKeys(keyList=['space'])
start_time_str = str(timedelta(seconds=core.getTime() - start_press_time))

# ---------- Resume Logic ----------
# Initialize logs and resume mechanism
trial_data = []
word_log = []
resume_trial = 0
postfix = ''

# If previous data exists, check how far it got and offer to resume (in case of previous crash)
try:
    if os.path.exists(data_filename):
        with open(data_filename, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            lines = list(reader)
            header_idx = next(i for i, l in enumerate(lines) if 'trial_num' in l)
            completed = [int(row[0]) for row in lines[header_idx + 1:] if row[0].isdigit()]
            if completed:
                resume_trial = max(completed)
                dlg_resume = gui.Dlg(title="Επανεκκίνηση;")
                dlg_resume.addText(f"Να συνεχίσει από το trial {resume_trial + 1};")
                dlg_resume.addField("Επανεκκίνηση;", choices=["Yes", "No"])
                resume = dlg_resume.show()
                if dlg_resume.OK and resume[0] == "Yes": # Mark resume point in logs
                    rt = core.getTime()
                    postfix = '_postcrash'
                    trial_data.append({'trial_num': '', 'sentence_id': 'RESUME_DETECTED', 'sentence': '',
                                       'question': '', 'correct_answer': '', 'response': '',
                                       'event_time': str(timedelta(seconds=rt)),
                                       'real_time': datetime.now().strftime('%H:%M:%S.%f')[:-3]})
                    word_log.append({'trial_num': '', 'sentence_id': 'RESUME_DETECTED', 'word': '',
                                     'event_time': str(timedelta(seconds=rt)),
                                     'real_time': datetime.now().strftime('%H:%M:%S.%f')[:-3]})

                else:
                    resume_trial = 0
except:
    # If any error happens here, ignore and proceed from beginning
    pass

# ---------- Start Timing ----------
# Record the start time of the main experiment
experiment_start = core.getTime()

# ---------- Block Setup ----------
# Split total trials into equal-sized blocks
total_trials = len(stimuli_df)
num_blocks = 4
block_size = total_trials // num_blocks

# ---------- Trial Loop ----------
try:
    for block in range(num_blocks):
        start = block * block_size
        end = total_trials if block == num_blocks - 1 else (block + 1) * block_size
        block_df = stimuli_df.iloc[start:end].reset_index(drop=True)

        for i, (_, row) in enumerate(block_df.iterrows()):
            trial_num = start + i
            print(f"Trial {trial_num + 1} of {total_trials}")  # Display trial progress in terminal
            if trial_num < resume_trial:
                continue # Skip trials already completed before a crash

            # Trial fixation cross
            win.flip()
            core.wait(0.250) # Blank screen duration
            visual.TextStim(win, text='+', color='black', height=50).draw()
            win.flip()
            core.wait(1.0) # Fixation cross duration
            win.flip()
            core.wait(0.1) # Blank screen duration

            # Retrieve trial content
            sentence_id = row['id']
            sentence = row['sentence']
            question = row.get('question', '')
            correct_answer = row.get('correct_answer', '')
            is_question = str(sentence_id).startswith("Q_")
            response = ''
            now_event = str(timedelta(seconds=core.getTime() - experiment_start))
            now_real = datetime.now().strftime('%H:%M:%S')

            # If the sentence is a question, display it and collect yes/no response
            if is_question:
                #Trigger for Question
                parallel.setData(254)
                # Short pulse du    ration using core.wait
                core.wait(0.01)  # Adjust the delay if needed
                # Reset the parallel port (clear the trigger)
                parallel.setData(0)
                stim = visual.TextStim(win, text=f"{sentence}\n\n(Πατήστε N για Ναι, O για Όχι)", color='black', height=28, wrapWidth=800) #Press N for yes, O for No
                stim.draw()
                win.flip()
                while True:
                    keys = event.getKeys()
                    # Pause feature during question
                    if 'escape' in keys:
                        pause_start = core.getTime() - experiment_start
                        timestamp = str(timedelta(seconds=pause_start))
                        real = datetime.now().strftime('%H:%M:%S.%f')[:-3]

                        word_log.append(
                            {'trial_num': '', 'sentence_id': 'PAUSE_START', 'word': '', 'event_time': timestamp,
                             'real_time': real})
                        trial_data.append(
                            {'trial_num': '', 'sentence_id': 'PAUSE_START', 'sentence': '', 'question': '',
                             'correct_answer': '', 'response': '', 'event_time': timestamp, 'real_time': real})

                        visual.TextStim(win, text='ΠΑΥΣΗ\nSPACE: συνέχεια, Q: έξοδος', height=30, color='black').draw()
                        win.flip()

                        while True:
                            cont_keys = event.waitKeys()
                            if 'q' in cont_keys:
                                raise KeyboardInterrupt("Experiment exited.")
                            elif 'space' in cont_keys:
                                pause_end = core.getTime() - experiment_start
                                timestamp = str(timedelta(seconds=pause_end))
                                real = datetime.now().strftime('%H:%M:%S.%f')[:-3]

                                word_log.append({'trial_num': '', 'sentence_id': 'PAUSE_RESUME', 'word': '',
                                                 'event_time': timestamp, 'real_time': real})
                                trial_data.append(
                                    {'trial_num': '', 'sentence_id': 'PAUSE_RESUME', 'sentence': '', 'question': '',
                                     'correct_answer': '', 'response': '', 'event_time': timestamp, 'real_time': real})
                                break

                    elif 'n' in keys or 'o' in keys:
                        response = keys[0]
                        break
            # Present sentence word-by-word, with 450ms per word
            else:
                words = sentence.split()
                #Trigger for Question
                parallel.setData(1)
                # Short pulse du    ration using core.wait
                core.wait(0.01)  # Adjust the delay if needed
                # Reset the parallel port (clear the trigger)
                parallel.setData(0)
                for word in words:
                    word_time = core.getTime() - experiment_start
                    visual.TextStim(win, text=word, color='black', height=40).draw()
                    parallel.setData(100)
                    win.flip()
                    word_log.append({'trial_num': trial_num + 1, 'sentence_id': sentence_id, 'word': word,
                                     'event_time': str(timedelta(seconds=word_time)),
                                     'real_time': datetime.now().strftime('%H:%M:%S.%f')[:-3]
})
                    # Check for pause during word display
                    for _ in range(45):
                        if 'escape' in event.getKeys():
                            pause_start = core.getTime() - experiment_start
                            timestamp = str(timedelta(seconds=pause_start))
                            real = datetime.now().strftime('%H:%M:%S.%f')[:-3]

                            word_log.append(
                                {'trial_num': '', 'sentence_id': 'PAUSE_START', 'word': '', 'event_time': timestamp,
                                 'real_time': real})
                            trial_data.append(
                                {'trial_num': '', 'sentence_id': 'PAUSE_START', 'sentence': '', 'question': '',
                                 'correct_answer': '', 'response': '', 'event_time': timestamp, 'real_time': real})

                            visual.TextStim(win, text='ΠΑΥΣΗ\nSPACE: συνέχεια, Q: έξοδος', height=30,
                                            color='black').draw()
                            win.flip()

                            while True:
                                k = event.waitKeys()
                                if 'q' in k:
                                    raise KeyboardInterrupt("Experiment exited.")
                                elif 'space' in k:
                                    pause_end = core.getTime() - experiment_start
                                    timestamp = str(timedelta(seconds=pause_end))
                                    real = datetime.now().strftime('%H:%M:%S.%f')[:-3]

                                    word_log.append({'trial_num': '', 'sentence_id': 'PAUSE_RESUME', 'word': '',
                                                     'event_time': timestamp, 'real_time': real})
                                    trial_data.append(
                                        {'trial_num': '', 'sentence_id': 'PAUSE_RESUME', 'sentence': '', 'question': '',
                                         'correct_answer': '', 'response': '', 'event_time': timestamp,
                                         'real_time': real})
                                    break
                        core.wait(0.01) # 10ms * 45 times of the loop = 450ms word duration
                        # To reset the trigger to 0 after 10ms
                        if _ == 10:
                            parallel.setData(0)
                    win.flip() #blank screen
                    core.wait(0.1) # Inter-word interval


            # Store response and trial metadata
            trial_data.append({
                'trial_num': trial_num + 1,
                'sentence_id': sentence_id,
                'sentence': sentence,
                'question': question,
                'correct_answer': correct_answer,
                'response': response,
                'event_time': now_event,
                'real_time': now_real
            })


        # ---------- Inter-block Break ----------
        if block < num_blocks - 1:
            break_start = core.getTime()
            word_log.append({'trial_num': '', 'sentence_id': f'BREAK_START_block{block + 1}', 'word': '',
                             'event_time': str(timedelta(seconds=break_start - experiment_start)),
                             'real_time': datetime.now().strftime('%H:%M:%S.%f')[:-3]
                             })
            trial_data.append({'trial_num': '', 'sentence_id': f'BREAK_START_block{block + 1}', 'sentence': '',
                               'question': '', 'correct_answer': '', 'response': '',
                               'event_time': str(timedelta(seconds=break_start - experiment_start)),
                               'real_time': datetime.now().strftime('%H:%M:%S.%f')[:-3]
                               })

            # Wait for participant to resume after break
            visual.TextStim(win, text='Διάλειμμα\nΠατήστε SPACE για συνέχεια.', height=30, color='black').draw()
            win.flip()
            event.waitKeys(keyList=['space'])
            break_end = core.getTime()
            word_log.append({'trial_num': '', 'sentence_id': f'BREAK_END_block{block + 1}', 'word': '',
                             'event_time': str(timedelta(seconds=break_end - experiment_start)),
                             'real_time': datetime.now().strftime('%H:%M:%S.%f')[:-3]
                             })
            trial_data.append({'trial_num': '', 'sentence_id': f'BREAK_END_block{block + 1}', 'sentence': '',
                               'question': '', 'correct_answer': '', 'response': '',
                               'event_time': str(timedelta(seconds=break_end - experiment_start)),
                               'real_time': datetime.now().strftime('%H:%M:%S.%f')[:-3]
                               })

# ---------- Crash Handling ----------
except Exception as e:
    print("Experiment crashed. Saving data...")
    traceback.print_exc()

# ---------- Save Data ----------
finally:
    # Calculate total duration
    total_time = str(timedelta(seconds=core.getTime() - experiment_start))
    # If the experiment resumed after a crash, '_postcrash' suffix is added to the filenames.
    # Resumed data is saved in a separate file and does not overwrite the original.
    final_data_file = data_filename.replace('.csv', f'{postfix}.csv')
    final_word_file = word_log_filename.replace('.csv', f'{postfix}.csv')

    # Write trial data to CSV
    with open(final_data_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([f"# First SPACE pressed at: {start_time_str}"])
        writer.writerow([f"# Experiment duration: {total_time}"])
        fieldnames = ['trial_num', 'sentence_id', 'sentence', 'question', 'correct_answer', 'response', 'event_time', 'real_time']
        writer.writerow(fieldnames)
        for row in trial_data:
            writer.writerow([row.get(col, '') for col in fieldnames])

    # Write word-by-word timing log
    with open(final_word_file, 'w', newline='', encoding='utf-8') as wf:
        writer = csv.DictWriter(wf, fieldnames=['trial_num', 'sentence_id', 'word', 'event_time', 'real_time'])
        writer.writeheader()
        writer.writerows(word_log)

    # Show end screen and exit
    visual.TextStim(win, text="Το πείραμα ολοκληρώθηκε.\n\nΕυχαριστούμε!", color='black', height=30).draw() #The experiment is over. Thank you!
    win.flip()
    event.waitKeys()
    win.close()
    core.quit()
