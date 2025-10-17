# Tasks: Paragraph Reformatter Modelfile

**Input**: Design documents from `/specs/001-paragraph-reformatter/`
**Prerequisites**: plan.md, spec.md, research.md, quickstart.md, data-model.md

**Tests**: No automated tests requested - manual validation only

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions
- **Modelfile location**: `Modelfiles/Modelfile-reformat` (repository root)
- **Test data**: `specs/001-paragraph-reformatter/test-data/` (for validation samples)
- **Validation scripts**: `specs/001-paragraph-reformatter/validation/` (for content preservation checks)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and validation script preparation

- [ ] T001 Create test data directory at `specs/001-paragraph-reformatter/test-data/`
- [ ] T002 Create validation scripts directory at `specs/001-paragraph-reformatter/validation/`
- [ ] T003 [P] Create sample unformatted text file at `specs/001-paragraph-reformatter/test-data/sample-continuous.txt` (continuous text, no paragraph breaks)
- [ ] T004 [P] Create sample short text file at `specs/001-paragraph-reformatter/test-data/sample-short.txt` (< 100 words)
- [ ] T005 [P] Create sample long text file at `specs/001-paragraph-reformatter/test-data/sample-long.txt` (> 2000 words)
- [ ] T006 [P] Create validation script at `specs/001-paragraph-reformatter/validation/check-preservation.sh` (word-for-word comparison)
- [ ] T007 [P] Create paragraph quality script at `specs/001-paragraph-reformatter/validation/check-quality.sh` (sentence count per paragraph)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core Modelfile that MUST be complete before ANY user story validation can proceed

**⚠️ CRITICAL**: No user story validation can begin until this phase is complete

- [ ] T008 Create base Modelfile at `Modelfiles/Modelfile-reformat` with FROM directive (llama3.2:latest)
- [ ] T009 Add SYSTEM instruction to `Modelfiles/Modelfile-reformat` with paragraph reformatting prompt from research.md
- [ ] T010 Add PARAMETER temperature 0.3 to `Modelfiles/Modelfile-reformat` for deterministic output
- [ ] T011 [P] Add PARAMETER top_p 0.9 to `Modelfiles/Modelfile-reformat` for controlled randomness
- [ ] T012 [P] Add PARAMETER repeat_penalty 1.1 to `Modelfiles/Modelfile-reformat` to prevent output echoing
- [ ] T013 Build the model with `ollama create transcriber-reformat -f Modelfiles/Modelfile-reformat`
- [ ] T014 Verify model creation with `ollama list` (should show transcriber-reformat)

**Checkpoint**: Foundation ready - model created and available for testing

---

## Phase 3: User Story 1 - Process Raw Transcript Text (Priority: P1) 🎯 MVP

**Goal**: Transform unstructured text from speech-to-text into well-organized paragraphs with logical breaks

**Independent Test**: Process a block of continuous unformatted text and verify output contains proper paragraph breaks based on topic shifts and natural content breaks

### Validation for User Story 1

**NOTE: Perform manual validation to ensure requirements are met**

- [ ] T015 [US1] Test with continuous text sample: `ollama run transcriber-reformat < specs/001-paragraph-reformatter/test-data/sample-continuous.txt > specs/001-paragraph-reformatter/test-data/output-continuous.txt`
- [ ] T016 [US1] Manually inspect `specs/001-paragraph-reformatter/test-data/output-continuous.txt` for logical paragraph breaks at topic shifts
- [ ] T017 [US1] Run preservation check: `bash specs/001-paragraph-reformatter/validation/check-preservation.sh test-data/sample-continuous.txt test-data/output-continuous.txt`
- [ ] T018 [US1] Run quality check: `bash specs/001-paragraph-reformatter/validation/check-quality.sh test-data/output-continuous.txt` (verify 3-8 sentences/paragraph average)

### Refinement for User Story 1 (if needed)

- [ ] T019 [US1] If paragraph breaks are too frequent: Increase temperature to 0.4-0.5 in `Modelfiles/Modelfile-reformat` and rebuild with `ollama create`
- [ ] T020 [US1] If paragraph breaks are too infrequent: Decrease temperature to 0.2 in `Modelfiles/Modelfile-reformat` and rebuild with `ollama create`
- [ ] T021 [US1] If content is modified: Review and strengthen SYSTEM prompt constraints in `Modelfiles/Modelfile-reformat` emphasizing "NEVER modify words"
- [ ] T022 [US1] Re-test after any refinements (repeat T015-T018)

**Checkpoint**: At this point, User Story 1 should be fully functional - continuous text gets properly formatted paragraphs

---

## Phase 4: User Story 2 - Handle Various Text Lengths (Priority: P2)

**Goal**: Process text of varying lengths (short notes to lengthy transcripts) without degradation in quality or performance

**Independent Test**: Process texts of different lengths and verify consistent paragraph structure quality across all inputs

### Validation for User Story 2

- [ ] T023 [P] [US2] Test with short text: `ollama run transcriber-reformat < specs/001-paragraph-reformatter/test-data/sample-short.txt > specs/001-paragraph-reformatter/test-data/output-short.txt`
- [ ] T024 [P] [US2] Test with long text: `ollama run transcriber-reformat < specs/001-paragraph-reformatter/test-data/sample-long.txt > specs/001-paragraph-reformatter/test-data/output-long.txt`
- [ ] T025 [US2] Verify short text is not over-segmented (inspect `specs/001-paragraph-reformatter/test-data/output-short.txt` manually)
- [ ] T026 [US2] Verify long text maintains topic coherence across paragraphs (inspect `specs/001-paragraph-reformatter/test-data/output-long.txt` manually)
- [ ] T027 [P] [US2] Run preservation check on short: `bash specs/001-paragraph-reformatter/validation/check-preservation.sh test-data/sample-short.txt test-data/output-short.txt`
- [ ] T028 [P] [US2] Run preservation check on long: `bash specs/001-paragraph-reformatter/validation/check-preservation.sh test-data/sample-long.txt test-data/output-long.txt`
- [ ] T029 [US2] Measure processing time for long text: `time ollama run transcriber-reformat < specs/001-paragraph-reformatter/test-data/sample-long.txt > /dev/null` (should be < 30 seconds for 2000 words)

### Performance Optimization for User Story 2 (if needed)

- [ ] T030 [US2] If long text processing exceeds 30s: Consider switching base model to `mistral:latest` in `Modelfiles/Modelfile-reformat` for faster inference
- [ ] T031 [US2] If model change needed: Update FROM directive in `Modelfiles/Modelfile-reformat` and rebuild with `ollama create transcriber-reformat -f Modelfiles/Modelfile-reformat`
- [ ] T032 [US2] Re-test all samples after model change to ensure quality maintained

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - handles any text length properly

---

## Phase 5: User Story 3 - Preserve Original Meaning (Priority: P1)

**Goal**: Improve structure without altering, removing, or adding content beyond formatting improvements

**Independent Test**: Compare word-for-word content before and after processing, verifying no additions, deletions, or substantive changes beyond paragraph structuring

### Validation for User Story 3

- [ ] T033 [P] [US3] Create test file with technical terms at `specs/001-paragraph-reformatter/test-data/sample-technical.txt` (includes code, URLs, special terms)
- [ ] T034 [P] [US3] Create test file with numbers/facts at `specs/001-paragraph-reformatter/test-data/sample-factual.txt` (dates, measurements, statistics)
- [ ] T035 [US3] Process technical file: `ollama run transcriber-reformat < specs/001-paragraph-reformatter/test-data/sample-technical.txt > specs/001-paragraph-reformatter/test-data/output-technical.txt`
- [ ] T036 [US3] Process factual file: `ollama run transcriber-reformat < specs/001-paragraph-reformatter/test-data/sample-factual.txt > specs/001-paragraph-reformatter/test-data/output-factual.txt`
- [ ] T037 [P] [US3] Run preservation check on technical: `bash specs/001-paragraph-reformatter/validation/check-preservation.sh test-data/sample-technical.txt test-data/output-technical.txt` (must show 100% match)
- [ ] T038 [P] [US3] Run preservation check on factual: `bash specs/001-paragraph-reformatter/validation/check-preservation.sh test-data/sample-factual.txt test-data/output-factual.txt` (must show 100% match)
- [ ] T039 [US3] Manually verify technical terms, URLs, code preserved exactly in `specs/001-paragraph-reformatter/test-data/output-technical.txt`
- [ ] T040 [US3] Manually verify numbers, dates, facts preserved exactly in `specs/001-paragraph-reformatter/test-data/output-factual.txt`

### Content Integrity Hardening for User Story 3 (if needed)

- [ ] T041 [US3] If any content modifications detected: Strengthen SYSTEM prompt in `Modelfiles/Modelfile-reformat` with additional "preserve code blocks", "preserve URLs", "preserve numbers" instructions
- [ ] T042 [US3] If modifications persist: Lower temperature to 0.1 in `Modelfiles/Modelfile-reformat` for maximum determinism
- [ ] T043 [US3] If modifications still occur: Add explicit examples to SYSTEM prompt showing input/output with preserved technical content
- [ ] T044 [US3] Re-test all preservation checks after any prompt changes

**Checkpoint**: All user stories should now be independently functional - content is 100% preserved

---

## Phase 6: Edge Cases & Robustness

**Purpose**: Handle special cases identified in spec.md edge cases section

- [ ] T045 [P] Create already-formatted sample at `specs/001-paragraph-reformatter/test-data/sample-formatted.txt` (text with existing paragraph breaks)
- [ ] T046 [P] Create mixed-language sample at `specs/001-paragraph-reformatter/test-data/sample-multilingual.txt` (English + special characters)
- [ ] T047 [P] Create single-sentence sample at `specs/001-paragraph-reformatter/test-data/sample-single.txt` (very short, no breaks needed)
- [ ] T048 Test already-formatted: `ollama run transcriber-reformat < specs/001-paragraph-reformatter/test-data/sample-formatted.txt > specs/001-paragraph-reformatter/test-data/output-formatted.txt`
- [ ] T049 Test multilingual: `ollama run transcriber-reformat < specs/001-paragraph-reformatter/test-data/sample-multilingual.txt > specs/001-paragraph-reformatter/test-data/output-multilingual.txt`
- [ ] T050 Test single-sentence: `ollama run transcriber-reformat < specs/001-paragraph-reformatter/test-data/sample-single.txt > specs/001-paragraph-reformatter/test-data/output-single.txt`
- [ ] T051 Verify already-formatted text preserves existing structure (manual inspection)
- [ ] T052 Verify multilingual text handles special characters correctly (manual inspection)
- [ ] T053 Verify single-sentence returns unchanged (manual comparison)

---

## Phase 7: Integration & Usage Documentation

**Purpose**: Integrate with existing transcriber pipeline and document usage

- [ ] T054 [P] Update README.md in repository root to mention transcriber-reformat model as optional tool
- [ ] T055 [P] Add usage examples to README.md showing how to use reformatter with transcripts
- [ ] T056 [P] Create example integration script at `scripts/reformat-transcript.sh` (optional helper for reformatting existing transcripts)
- [ ] T057 Test integration script with real transcript from `~/Resources/Transcripts/text-unprocessed/` (if available)
- [ ] T058 Document model info in quickstart.md: `ollama show transcriber-reformat --modelfile >> specs/001-paragraph-reformatter/quickstart.md`

---

## Phase 8: Polish & Final Validation

**Purpose**: Final improvements and comprehensive validation

- [ ] T059 Run full validation suite on all test samples (re-run all preservation and quality checks from T017, T018, T027, T028, T037, T038)
- [ ] T060 [P] Create summary report at `specs/001-paragraph-reformatter/validation/test-results.md` documenting all validation outcomes
- [ ] T061 [P] Measure and document performance for each sample size in test-results.md
- [ ] T062 Review SYSTEM prompt in `Modelfiles/Modelfile-reformat` for clarity and completeness
- [ ] T063 Add inline comments to `Modelfiles/Modelfile-reformat` explaining each parameter choice
- [ ] T064 Verify model listed in `ollama list` output
- [ ] T065 Test model can be updated: recreate with `ollama create transcriber-reformat -f Modelfiles/Modelfile-reformat` (should replace cleanly)
- [ ] T066 [P] Update CLAUDE.md with final model status (change from "In Development" to "Complete")
- [ ] T067 Final checkpoint: Run quickstart.md examples manually to ensure all documented usage works

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup (test infrastructure needed) - BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational phase completion
- **User Story 2 (Phase 4)**: Depends on Foundational phase completion - Can run in parallel with US1
- **User Story 3 (Phase 5)**: Depends on Foundational phase completion - Can run in parallel with US1, US2
- **Edge Cases (Phase 6)**: Depends on US1, US2, US3 completion (uses same model configuration)
- **Integration (Phase 7)**: Depends on all user stories being validated
- **Polish (Phase 8)**: Depends on all previous phases

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - Independent of US1, US3
- **User Story 3 (P1)**: Can start after Foundational (Phase 2) - Independent of US1, US2

**KEY INSIGHT**: All three user stories are completely independent and can be validated in parallel after Phase 2 completes.

### Within Each User Story

- Validation tasks before refinement tasks
- Preservation checks can run in parallel with quality checks
- Model refinement requires rebuild before re-testing
- Each story complete and validated independently before moving to next

### Parallel Opportunities

- **Phase 1**: Tasks T003-T007 (all test data and validation scripts) can run in parallel
- **Phase 2**: Tasks T011-T012 (PARAMETER settings) can run in parallel
- **Phase 3 (US1)**: Tasks T019-T021 (refinement options) are conditional - only if needed
- **Phase 4 (US2)**: Tasks T023-T024 (short/long testing) can run in parallel, T027-T028 (preservation checks) can run in parallel
- **Phase 5 (US3)**: Tasks T033-T034 (create test files) can run in parallel, T037-T038 (preservation checks) can run in parallel
- **Phase 6**: Tasks T045-T047 (create edge case files) can run in parallel
- **Phase 7**: Tasks T054-T056 (documentation) can run in parallel
- **Phase 8**: Tasks T060-T061 (reporting) can run in parallel

---

## Parallel Example: User Story Validation

```bash
# After Phase 2 completes, launch all three user story validations in parallel:

# US1: Process raw transcript text
Task: "Test with continuous text sample using ollama run transcriber-reformat"
Task: "Run preservation check on continuous text"

# US2: Handle various text lengths
Task: "Test with short text using ollama run transcriber-reformat"
Task: "Test with long text using ollama run transcriber-reformat"

# US3: Preserve original meaning
Task: "Process technical file using ollama run transcriber-reformat"
Task: "Process factual file using ollama run transcriber-reformat"

# All validations can proceed independently
```

---

## Implementation Strategy

### MVP First (User Story 1 + User Story 3 Only)

1. Complete Phase 1: Setup (test infrastructure)
2. Complete Phase 2: Foundational (create and build Modelfile) - CRITICAL
3. Complete Phase 3: User Story 1 (core reformatting works)
4. Complete Phase 5: User Story 3 (content preservation verified)
5. **STOP and VALIDATE**: Test both US1 and US3 together
6. You now have a working paragraph reformatter with content integrity guarantee

**Why this MVP**: US1 provides core value (formatting), US3 ensures trust (no content changes). US2 (text lengths) is nice-to-have for edge cases.

### Incremental Delivery

1. Complete Setup + Foundational → Model ready
2. Add User Story 1 + User Story 3 → Test together → **MVP DONE** (core feature working with integrity)
3. Add User Story 2 → Test independently → **COMPLETE** (handles all text lengths)
4. Add Edge Cases (Phase 6) → Robustness verified
5. Add Integration (Phase 7) → Pipeline integration ready
6. Polish (Phase 8) → Production ready

### Parallel Team Strategy

Since this is a single Modelfile project, parallel work is limited but possible:

1. **Developer A**: Create test data and validation scripts (Phase 1)
2. **Developer B**: Create Modelfile configuration (Phase 2)
3. After Phase 2:
   - **Developer A**: Validate US1 + US2 (formatting and length handling)
   - **Developer B**: Validate US3 + Edge Cases (content preservation)
   - **Developer C**: Integration and documentation (Phase 7)
4. All converge on final validation (Phase 8)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Manual validation required - no automated test suite for this feature
- Commit after each phase completion or logical group
- Stop at any checkpoint to validate story independently
- Model rebuilds (T013, T019, T020, T021, T030, T031, etc.) replace previous version cleanly
- Validation scripts are reusable across all test scenarios
