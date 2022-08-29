import nlpaug.augmenter.word as naw
import tqdm

input_texts = []
n_augmentations = 5
contextual_aug = naw.ContextualWordEmbsAug(model_path='bert-base-uncased', action="substitute")
synonym_aug = naw.SynonymAug(aug_src='wordnet')

# read inputs
with open("input.txt") as input_file:
    input_texts = input_file.readlines()

# write augmented texts
f = open("output.txt", "w")
for text in tqdm.tqdm(input_texts):
    if text[0:4] != 'SKIP':
        f.write(f"PHRASE: {text}\n")

        f.write("CONTEXTUAL\n")
        tmp_aug = contextual_aug.augment(text, n=n_augmentations)
        for t in tmp_aug:
            f.write(t + '\n')

        f.write("SYNONYM\n")
        tmp_aug = synonym_aug.augment(text, n=n_augmentations)
        for t in tmp_aug:
            f.write(t + '\n')
        f.write("\n#############################################################\n\n")
    else:
        f.write('\n------------------------------------------------------------------\n\n\n')

f.close()