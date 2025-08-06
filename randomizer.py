import pandas as pd
import random
import os


def randomize(participant_id: str):
    input_file = 'stimuli.csv'
    output_dir = 'logs_order'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    question_interval = 26
    max_repeat = 1
    max_attempts = 1000

    df = pd.read_csv(input_file)
    df = df.fillna('')

    has_question = df['question'].str.strip() != ''
    question_pairs = df[has_question].copy()
    plain_sentences = df[~has_question].copy()

    shuffled_questions = question_pairs.sample(frac=1).reset_index(drop=True)

    def has_cluster(series, max_repeat=2):
        count = 1
        for i in range(1, len(series)):
            if series[i] == series[i - 1]:
                count += 1
                if count > max_repeat:
                    return True
            count = 1
        return False

    for attempt in range(max_attempts):
        random_seed = random.randint(0, 10000)
        shuffled_plain = plain_sentences.sample(frac=1, random_state=random_seed).reset_index(drop=True)
        if not has_cluster(shuffled_plain['condition'].tolist(), max_repeat=max_repeat):
            break
    else:
        print('Could not find a valid shuffle without condition clusters. Using last attempt.')

    final_rows = []
    question_pointer = 0
    plain_pointer = 0
    total_items = len(df) + len(question_pairs)
    insert_positions = list(range(question_interval, total_items, question_interval + 2))

    trial_num = 1
    current_idx = 0
    insert_idx = 0

    while len(final_rows) < total_items:
        should_insert_question = (
            insert_idx < len(insert_positions)
            and current_idx == insert_positions[insert_idx]
        )

        if should_insert_question and question_pointer < len(shuffled_questions):
            q_row = shuffled_questions.iloc[question_pointer]

            # Sentence
            final_rows.append({
                'trial_num': trial_num,
                'id': q_row['id'],
                'condition': q_row['condition'],
                'sentence': q_row['sentence'],
                'correct_answer': '',
                'condition_code': q_row['condition_code'],
                'word_count': q_row['word_count'],
                'target_word': q_row['target_word']
            })
            trial_num += 1

            # Question (condition_code is 50 for questions)
            final_rows.append({
                'trial_num': trial_num,
                'id': f'Q_{q_row["id"]}',
                'condition': q_row['condition'],
                'sentence': q_row['question'],
                'correct_answer': q_row['correct_answer'],
                'condition_code': 50,
                'word_count': q_row['word_count'],
                'target_word': q_row['target_word']
            })

            question_pointer += 1
            current_idx += 2
            insert_idx += 1
            continue

        if plain_pointer < len(shuffled_plain):
            f_row = shuffled_plain.iloc[plain_pointer]
            final_rows.append({
                'trial_num': trial_num,
                'id': f_row['id'],
                'condition': f_row['condition'],
                'sentence': f_row['sentence'],
                'correct_answer': '',
                'condition_code': f_row['condition_code'],
                'word_count': f_row['word_count'],
                'target_word': f_row['target_word']
            })
            trial_num += 1
            plain_pointer += 1
            current_idx += 1
        elif question_pointer < len(shuffled_questions):
            q_row = shuffled_questions.iloc[question_pointer]

            final_rows.append({
                'trial_num': trial_num,
                'id': q_row['id'],
                'condition': q_row['condition'],
                'sentence': q_row['sentence'],
                'correct_answer': '',
                'condition_code': q_row['condition_code'],
                'word_count': q_row['word_count'],
                'target_word': q_row['target_word']
            })
            trial_num += 1

            final_rows.append({
                'trial_num': trial_num,
                'id': f'Q_{q_row["id"]}',
                'condition': q_row['condition'],
                'sentence': q_row['question'],
                'correct_answer': q_row['correct_answer'],
                'condition_code': q_row['condition_code'],
                'word_count': q_row['word_count'],
                'target_word': q_row['target_word']
            })
            trial_num += 1

            question_pointer += 1
            current_idx += 2
        else:
            break

    # Save to CSV
    output_path = os.path.join(output_dir, f'{participant_id}_randomized_list.csv')
    output_df = pd.DataFrame(final_rows)[[
        'trial_num', 'id', 'condition', 'condition_code',
        'word_count', 'target_word', 'sentence', 'correct_answer'
    ]]
    output_df.to_csv(output_path, index=False, encoding='utf-8')

    print('Randomized list saved.')

    return output_df


if __name__ == '__main__':
    randomize('testing')
