# --- Imports ---
import os
import csv
import traceback
from datetime import timedelta, datetime
import platform

import pandas as pd
from psychopy import visual, core, event, gui, logging
from randomizer import randomize

# --- Trigger setup ---
USE_PARALLEL = platform.system() == 'Windows'

if USE_PARALLEL:
    from psychopy import parallel
    parallel.setPortAddress(0x3FE8)

    def send_trigger(code):
        parallel.setData(code)
        core.wait(0.005)
        parallel.setData(0)
else:
    logging.warning('Parallel port not available on this system. Using dummy trigger.')

    def send_trigger(code):
        logging.exp(f'[Mock trigger] Code {code} would have been sent.')


# --- Pause/resume helper ---
def check_pause(experiment_start, trial_data, word_log, win):
    if 'escape' in event.getKeys():
        pause_start = core.getTime() - experiment_start
        timestamp = str(timedelta(seconds=pause_start))
        real = datetime.now().strftime('%H:%M:%S.%f')[:-3]

        trial_data.append({
            'trial_num': '', 'sentence_id': 'PAUSE_START', 'sentence': '',
            'question': '', 'correct_answer': '', 'response': '',
            'event_time': timestamp, 'real_time': real
        })
        word_log.append({
            'trial_num': '', 'sentence_id': 'PAUSE_START', 'word': '',
            'event_time': timestamp, 'real_time': real
        })

        visual.TextStim(win, text='ΠΑΥΣΗ\nSPACE: συνέχεια, Q: έξοδος', height=30, color='black').draw()
        win.flip()

        while True:
            keys = event.waitKeys()
            if 'q' in keys:
                raise KeyboardInterrupt("Experiment exited by user.")
            elif 'space' in keys:
                pause_end = core.getTime() - experiment_start
                timestamp = str(timedelta(seconds=pause_end))
                real = datetime.now().strftime('%H:%M:%S.%f')[:-3]

                trial_data.append({
                    'trial_num': '', 'sentence_id': 'PAUSE_RESUME', 'sentence': '',
                    'question': '', 'correct_answer': '', 'response': '',
                    'event_time': timestamp, 'real_time': real
                })
                word_log.append({
                    'trial_num': '', 'sentence_id': 'PAUSE_RESUME', 'word': '',
                    'event_time': timestamp, 'real_time': real
                })
                break


# --- Participant info ---
participant_info = {'Participant ID': ''}
dlg = gui.DlgFromDict(dictionary=participant_info, title='Participant Info')
if not dlg.OK:
    core.quit()

participant_id = participant_info['Participant ID']
output_dir = 'logs_experiment'
os.makedirs(output_dir, exist_ok=True)

data_filename = os.path.join(output_dir, f'{participant_id}_data.csv')
word_log_filename = os.path.join(output_dir, f'{participant_id}_word_log.csv')
stimuli_path = f'logs_order/{participant_id}_randomized_list.csv'
os.makedirs(os.path.dirname(stimuli_path), exist_ok=True)

# --- Create window and show instructions ---
win = visual.Window(fullscr=False, color='white', units='pix')

instruction_text = (
    "Καλωσορίσατε!\n\n"
    "Σε αυτό το πείραμα θα εμφανίζονται προτάσεις λέξη-λέξη.\n\n"
    "Πρέπει απλώς να τις διαβάζετε από μέσα σας.\n\n"
    "Κάποιες φορές θα εμφανίζονται ερωτήσεις. "
    "Απαντήστε πατώντας 'N' για Ναι ή 'O' για Όχι.\n\n"
    "Πατήστε SPACE για να ξεκινήσετε."
)
visual.TextStim(win, text=instruction_text, color='black', height=30, wrapWidth=800).draw()
win.flip()

start_press_time = core.getTime()
event.waitKeys(keyList=['space'])
start_time_str = str(timedelta(seconds=core.getTime() - start_press_time))


# --- Resume logic ---
trial_data = []
word_log = []
resume_trial = 0
postfix = ''

if os.path.exists(data_filename):
    with open(data_filename, 'r', encoding='utf-8') as f:
        lines = list(csv.reader(f))
        header_idx = next(i for i, row in enumerate(lines) if 'trial_num' in row)
        completed = [int(row[0]) for row in lines[header_idx + 1:] if row[0].isdigit()]

        if completed:
            resume_trial = max(completed)
            dlg_resume = gui.Dlg(title='Resume experiment?')
            dlg_resume.addText(f'Participant ID already exists. Resume from trial {resume_trial + 1}?')
            dlg_resume.addField('Resume:', choices=['Yes', 'No'])
            response = dlg_resume.show()

            if dlg_resume.OK and response[0] == 'Yes':
                postfix = '_postcrash'
                timestamp = str(timedelta(seconds=core.getTime()))
                real = datetime.now().strftime('%H:%M:%S.%f')[:-3]

                trial_data.append({
                    'trial_num': '', 'sentence_id': 'RESUME_DETECTED', 'sentence': '',
                    'question': '', 'correct_answer': '', 'response': '',
                    'event_time': timestamp, 'real_time': real
                })
                word_log.append({
                    'trial_num': '', 'sentence_id': 'RESUME_DETECTED', 'word': '',
                    'event_time': timestamp, 'real_time': real
                })
            else:
                resume_trial = 0

    stimuli_df = pd.read_csv(stimuli_path)
else:
    stimuli_df = randomize(participant_id)
    stimuli_df.to_csv(stimuli_path, index=False)

# --- Timing setup ---
experiment_start = core.getTime()

# --- Block setup ---
total_trials = len(stimuli_df)
num_blocks = 4
block_size = total_trials // num_blocks

fieldnames = ['trial_num', 'sentence_id', 'sentence', 'question',
              'correct_answer', 'response', 'event_time', 'real_time']

# --- Trial loop ---
try:
    for block in range(num_blocks):
        start = block * block_size
        end = total_trials if block == num_blocks - 1 else (block + 1) * block_size
        block_df = stimuli_df.iloc[start:end].reset_index(drop=True)

        for i, (_, row) in enumerate(block_df.iterrows()):
            trial_num = start + i
            if trial_num < resume_trial:
                continue

            win.flip()
            core.wait(0.25)
            visual.TextStim(win, text='+', color='black', height=50).draw()
            win.flip()
            core.wait(1.0)
            win.flip()
            core.wait(0.1)

            sentence_id = row['id']
            sentence = row['sentence']
            question = row.get('question', '')
            correct_answer = row.get('correct_answer', '')
            is_question = str(sentence_id).startswith('Q_')
            response = ''
            now_event = str(timedelta(seconds=core.getTime() - experiment_start))
            now_real = datetime.now().strftime('%H:%M:%S')

            if is_question:
                send_trigger(254)
                stim = visual.TextStim(
                    win,
                    text=f'{sentence}\n\n(Πατήστε N για Ναι, O για Όχι)',
                    color='black',
                    height=28,
                    wrapWidth=800
                )
                stim.draw()
                win.flip()

                while True:
                    keys = event.getKeys()
                    if 'escape' in keys:
                        check_pause(experiment_start, trial_data, word_log, win)
                    elif 'n' in keys or 'o' in keys:
                        response = keys[0]
                        break
            else:
                words = sentence.split()
                send_trigger(1)
                for word in words:
                    word_time = core.getTime() - experiment_start
                    visual.TextStim(win, text=word, color='black', height=40).draw()
                    send_trigger(100)
                    win.flip()

                    word_log_entry = {
                        'trial_num': trial_num + 1,
                        'sentence_id': sentence_id,
                        'word': word,
                        'event_time': str(timedelta(seconds=word_time)),
                        'real_time': datetime.now().strftime('%H:%M:%S.%f')[:-3]
                    }
                    word_log.append(word_log_entry)

                    with open(word_log_filename, 'a', newline='', encoding='utf-8') as wf:
                        writer = csv.DictWriter(wf, fieldnames=word_log_entry.keys())
                        if wf.tell() == 0:
                            writer.writeheader()
                        writer.writerow(word_log_entry)

                    for _ in range(45):  # 450ms duration in 10ms steps
                        check_pause(experiment_start, trial_data, word_log, win)
                        core.wait(0.01)

                    win.flip()
                    core.wait(0.1)

            trial_entry = {
                'trial_num': trial_num + 1,
                'sentence_id': sentence_id,
                'sentence': sentence,
                'question': question,
                'correct_answer': correct_answer,
                'response': response,
                'event_time': now_event,
                'real_time': now_real
            }
            trial_data.append(trial_entry)

            with open(data_filename, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                if f.tell() == 0:
                    writer.writeheader()
                writer.writerow(trial_entry)

        if block < num_blocks - 1:
            visual.TextStim(win, text='Διάλειμμα\nΠατήστε SPACE για συνέχεια.',
                            height=30, color='black').draw()
            win.flip()
            event.waitKeys(keyList=['space'])

except Exception as e:
    print('Experiment crashed. Saving data...')
    traceback.print_exc()

finally:
    total_time = str(timedelta(seconds=core.getTime() - experiment_start))
    final_data_file = data_filename.replace('.csv', f'{postfix}.csv')
    final_word_file = word_log_filename.replace('.csv', f'{postfix}.csv')

    with open(final_data_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([f'# First SPACE pressed at: {start_time_str}'])
        writer.writerow([f'# Experiment duration: {total_time}'])
        writer.writerow(fieldnames)
        for row in trial_data:
            writer.writerow([row.get(col, '') for col in fieldnames])

    with open(final_word_file, 'w', newline='', encoding='utf-8') as wf:
        writer = csv.DictWriter(wf, fieldnames=['trial_num', 'sentence_id', 'word', 'event_time', 'real_time'])
        writer.writeheader()
        writer.writerows(word_log)

    visual.TextStim(
        win,
        text="Το πείραμα ολοκληρώθηκε.\n\nΕυχαριστούμε!",
        color='black',
        height=30).draw()

    win.flip()
    event.waitKeys()
    win.close()
    core.quit()