from ttpxhunter.training import TrainingExample, load_mitre_sentence_dataset, stratified_split


def test_load_mitre_sentence_dataset_builds_stable_label_mapping(tmp_path) -> None:
    path = tmp_path / "mitre.csv"
    path.write_text(
        "Technique ID,Technique Name,Sentences\n"
        "T1002,Two,second sentence\n"
        "T1001,One,first sentence\n"
        "T1001,One,another first sentence\n",
        encoding="utf-8",
    )

    examples, label_dict, name_map = load_mitre_sentence_dataset(
        path,
        label_dict_path=None,
        limit_per_class=1,
    )

    assert label_dict == {"T1001": 0, "T1002": 1}
    assert name_map == {"T1002": "Two", "T1001": "One"}
    assert len(examples) == 2
    assert {example.ttp_id for example in examples} == {"T1001", "T1002"}


def test_stratified_split_keeps_train_and_validation_examples() -> None:
    examples = [
        TrainingExample("a", "T1001", 0),
        TrainingExample("b", "T1001", 0),
        TrainingExample("c", "T1002", 1),
        TrainingExample("d", "T1002", 1),
    ]

    train, validation = stratified_split(examples, validation_ratio=0.5, seed=1)

    assert len(train) == 2
    assert len(validation) == 2
    assert {example.label_id for example in train} == {0, 1}
    assert {example.label_id for example in validation} == {0, 1}
