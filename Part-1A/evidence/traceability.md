# Part 1A Traceability: Acceptance Criteria → Tests → Specification → Tasks → Implementation

| AC    | Test function                                    | Spec section (FR/NFR ID) | Task ID (T0xx)   | Source file/function                                                                                                            |
| ----- | ------------------------------------------------ | ------------------------ | ---------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| AC-01 | test_ac01_add_defaults                           | FR-001                   | T007, T009       | src/todo/service.py — add_task(), normalize_priority(), normalize_status(), normalize_tags(); src/todo/cli.py — main()          |
| AC-02 | test_ac02_title_is_trimmed                       | FR-001, FR-002           | T007, T009       | src/todo/service.py — normalize_title(), add_task()                                                                             |
| AC-03 | test_ac03_invalid_title_rejected                 | FR-002                   | T007, T009       | src/todo/service.py — normalize_title()                                                                                         |
| AC-03 | test_ac03_title_boundary_100_ok                  | FR-002                   | T007, T009       | src/todo/service.py — normalize_title()                                                                                         |
| AC-04 | test_ac04_ids_sequential_and_never_reused        | FR-003, FR-009           | T009, T012, T021 | src/todo/service.py — add_task(), delete_task(); src/todo/store.py — read_store(), write_store()                                |
| AC-05 | test_ac05_invalid_priority_rejected              | FR-004                   | T007, T009       | src/todo/service.py — normalize_priority()                                                                                      |
| AC-06 | test_ac06_tags_normalised_and_deduplicated       | FR-005                   | T007, T010       | src/todo/service.py — normalize_tags()                                                                                          |
| AC-07 | test_ac07_invalid_tag_rejected                   | FR-005                   | T007, T010       | src/todo/service.py — normalize_tags()                                                                                          |
| AC-08 | test_ac08_max_ten_tags                           | FR-005                   | T010             | src/todo/service.py — normalize_tags()                                                                                          |
| AC-09 | test_ac09_list_default_order_by_id               | FR-006                   | T014             | src/todo/service.py — list_tasks()                                                                                              |
| AC-10 | test_ac10_filter_by_tag                          | FR-006                   | T015             | src/todo/service.py — list_tasks()                                                                                              |
| AC-11 | test_ac11_filter_by_status                       | FR-006                   | T016             | src/todo/service.py — list_tasks(), normalize_status()                                                                          |
| AC-12 | test_ac12_sort_by_priority_high_first_ties_by_id | FR-006                   | T017             | src/todo/service.py — list_tasks()                                                                                              |
| AC-13 | test_ac13_filter_and_sort_combine                | FR-006                   | T015, T017       | src/todo/service.py — list_tasks()                                                                                              |
| AC-14 | test_ac14_invalid_sort_or_status_filter_rejected | FR-006                   | T016, T018       | src/todo/service.py — list_tasks(), normalize_status(); src/todo/cli.py — \_parse_list_arguments(), main()                      |
| AC-15 | test_ac15_get_existing_and_missing               | FR-007                   | T004, T011       | src/todo/service.py — get_task(), \_task_lookup(); src/todo/errors.py — NotFoundError                                           |
| AC-16 | test_ac16_malformed_id_is_validation_error       | FR-007                   | T007, T011       | src/todo/service.py — normalize_id(); src/todo/errors.py — ValidationError                                                      |
| AC-17 | test_ac17_update_changes_only_given_fields       | FR-008                   | T007, T011       | src/todo/service.py — update_task(), normalize_title(), normalize_priority(), normalize_tags()                                  |
| AC-18 | test_ac18_update_requires_a_field_and_validates  | FR-008                   | T007, T011       | src/todo/service.py — update_task(); src/todo/errors.py — ValidationError                                                       |
| AC-19 | test_ac19_delete                                 | FR-009                   | T012             | src/todo/service.py — delete_task(), \_task_lookup(); src/todo/errors.py — NotFoundError                                        |
| AC-20 | test_ac20_allowed_transitions                    | FR-010                   | T019, T020       | src/todo/service.py — change_status(), normalize_status(); src/todo/cli.py — main()                                             |
| AC-21 | test_ac21_forbidden_transitions                  | FR-010                   | T019, T020       | src/todo/service.py — change_status(); src/todo/errors.py — InvalidTransitionError                                              |
| AC-22 | test_ac22_unknown_status_value                   | FR-010                   | T019, T020       | src/todo/service.py — change_status(), normalize_status(), \_task_lookup(); src/todo/errors.py — ValidationError, NotFoundError |
| AC-23 | test_ac23_persists_between_invocations           | FR-011, FR-015           | T005, T021       | src/todo/store.py — read_store(), write_store(); src/todo/cli.py — main()                                                       |
| AC-24 | test_ac24_corrupt_file_exit_4_and_untouched      | FR-012                   | T005, T022       | src/todo/store.py — read_store(), \_task_is_valid(); src/todo/errors.py — StorageError                                          |
| AC-24 | test_ac24_wrong_structure_exit_4                 | FR-012                   | T005, T022       | src/todo/store.py — read_store(), \_task_is_valid(); src/todo/errors.py — StorageError                                          |
| AC-25 | test_ac25_failed_command_does_not_modify_file    | FR-012, FR-015           | T006, T023       | src/todo/store.py — write_store(); src/todo/service.py — validation and mutation functions                                      |
| AC-26 | test_ac26_no_temp_files_left_behind              | FR-015                   | T006             | src/todo/store.py — write_store()                                                                                               |
| AC-27 | test_ac27_task_object_shape                      | FR-013                   | T007, T013, T021 | src/todo/service.py — add_task(), update_task(); src/todo/store.py — \_task_is_valid()                                          |
| AC-28 | test_ac28_unknown_command_is_validation_error    | FR-013, FR-014           | T004, T008, T024 | src/todo/cli.py — main(), \_emit_json(); src/todo/errors.py — TodoError, ValidationError                                        |
| AC-29 | test_ac29_module_entrypoint                      | FR-014                   | T002, T024       | src/todo/**main**.py; src/todo/cli.py — main()                                                                                  |

## Traceability notes

- Functional Requirement IDs are taken from specs/001-smart-todo/spec.md.
- Task IDs are taken from specs/001-smart-todo/tasks.md.
- Test function names are taken from tests/test_contract_cli.py.
- Source file and function names are mapped to the implemented code under src/todo/.
- Harness execution evidence is retained in evidence/harness-results/.
- Initial and final implementation snapshots are retained in evidence/initial-generation/ and evidence/final-generation/.
