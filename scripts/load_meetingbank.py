from __future__ import annotations

from datasets import load_dataset


def main() -> None:
    ds = load_dataset("huuuyeah/meetingbank")
    print("Dataset loaded.")
    print(ds)
    print("train columns:", ds["train"].column_names)
    print("train size:", len(ds["train"]))
    print("validation size:", len(ds["validation"]))
    print("test size:", len(ds["test"]))
    print("\nFirst train sample:")
    print(ds["train"][0])


if __name__ == "__main__":
    main()
