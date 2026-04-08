from __future__ import annotations

import argparse
import csv
from pathlib import Path


def split_csv(source: Path, output_dir: Path, rows_per_file: int) -> list[Path]:
    if rows_per_file < 1:
        raise ValueError("rows_per_file must be at least 1")

    output_dir.mkdir(parents=True, exist_ok=True)

    created_files: list[Path] = []
    with source.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if header is None:
            raise ValueError(f"{source} is empty")

        file_index = 1
        row_index = 0
        writer = None
        out_handle = None

        try:
            for row in reader:
                if row_index % rows_per_file == 0:
                    if out_handle is not None:
                        out_handle.close()
                    target = output_dir / f"{source.stem}.part{file_index:03d}{source.suffix}"
                    out_handle = target.open("w", newline="", encoding="utf-8")
                    writer = csv.writer(out_handle)
                    writer.writerow(header)
                    created_files.append(target)
                    file_index += 1
                writer.writerow(row)
                row_index += 1
        finally:
            if out_handle is not None:
                out_handle.close()

    return created_files


def main() -> None:
    parser = argparse.ArgumentParser(description="Split a CSV into smaller CSV files.")
    parser.add_argument("source", type=Path, help="Path to the CSV file to split.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Directory for split files. Defaults to <source stem>_splits next to the source file.",
    )
    parser.add_argument(
        "--rows-per-file",
        type=int,
        default=100_000,
        help="Number of data rows per split file.",
    )
    args = parser.parse_args()

    source = args.source.resolve()
    output_dir = args.output_dir or source.with_name(f"{source.stem}_splits")
    created_files = split_csv(source, output_dir, args.rows_per_file)

    print(f"Created {len(created_files)} files in {output_dir}")
    for file_path in created_files:
        print(file_path)


if __name__ == "__main__":
    main()
