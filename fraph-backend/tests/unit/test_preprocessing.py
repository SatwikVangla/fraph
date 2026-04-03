from pathlib import Path

from app.services.preprocessing import preprocess_dataset, profile_dataset, save_mapping_overrides


def test_profile_dataset_infers_columns_and_honors_mapping_overrides(tmp_path: Path) -> None:
    dataset_path = tmp_path / 'transactions.csv'
    dataset_path.write_text(
        '\n'.join(
            [
                'payer_id,payee_id,manual_sender,payment_value,fraud_flag,event_time',
                'alice,bob,team-a,125.5,0,2026-01-01T00:00:00',
                'carol,dave,team-b,210.0,1,2026-01-01T01:00:00',
            ]
        )
    )

    save_mapping_overrides(dataset_path, {'sender_column': 'manual_sender'})
    profile = profile_dataset(dataset_path)

    assert profile.row_count == 2
    assert profile.amount_column == 'payment_value'
    assert profile.sender_column == 'manual_sender'
    assert profile.receiver_column == 'payee_id'
    assert profile.label_column == 'fraud_flag'
    assert profile.step_column == 'event_time'


def test_preprocess_dataset_builds_normalized_frame_with_generated_ids(tmp_path: Path) -> None:
    dataset_path = tmp_path / 'payments.csv'
    dataset_path.write_text(
        '\n'.join(
            [
                'origin_account,destination_account,amount,isFraud,event_time',
                'acct-1,acct-2,10.5,1,2026-02-01T10:00:00',
                'acct-2,acct-3,4.0,0,2026-02-01T10:15:00',
            ]
        )
    )

    prepared, profile = preprocess_dataset(dataset_path)

    assert profile.sender_column == 'origin_account'
    assert profile.receiver_column == 'destination_account'
    assert prepared['transaction_id'].tolist() == ['txn-1', 'txn-2']
    assert prepared['sender'].tolist() == ['acct-1', 'acct-2']
    assert prepared['receiver'].tolist() == ['acct-2', 'acct-3']
    assert prepared['amount'].tolist() == [10.5, 4.0]
    assert prepared['step'].tolist() == [0.0, 900.0]
    assert prepared['label'].tolist() == [True, False]
