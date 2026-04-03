from app.utils.helpers import slugify_name


def test_slugify_name_normalizes_text_and_falls_back_for_empty_input() -> None:
    assert slugify_name(' Fraud Dataset 2026!.csv ') == 'fraud-dataset-2026-csv'
    assert slugify_name('   ') == 'dataset'
