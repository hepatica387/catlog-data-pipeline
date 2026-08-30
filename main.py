from src import (
    run_crawling,
    run_extract,
    run_load,
    run_preprocess,
)


def main():
    batch_dir = run_crawling()

    parsed_file = run_extract(batch_dir)

    processed_file = run_preprocess(parsed_file.parent)

    run_load(processed_file)


if __name__ == "__main__":
    main()
