## Unreleased

### Feat

- no longer need manipulate path during import
- uiucprescon.ocr.utils.pixScaleToSize()
- uiucprescon.ocr.utils.pixScaleToSize()
- PDFBuilder.add_page() can take either a file name or an Image

### Fix

- remove pdf_writer

### Refactor

- clean up c++ wrapper file
- optimize header imports
- use namespaced exceptions
- all c++ code is in namespace uiucprescon

## v0.2.0 (2026-07-29)

### Feat

- pdf can be generated with PDFBuilder()

### Fix

- image_lib_versions() can parse versions that include parentheses
- build_mac_wheel.sh now explicitly make non-freethreaded versions if the version number does not include a "t" at end
- build_mac_wheel.sh now explicitly make non-freethreaded versions if the version number does not include a "t" at end

### Refactor

- python dev dependencies are split up into type-checking and linting

## v0.1.5 (2025-12-16)

### Refactor

- make src directory the source root
- All build scripts are located in scripts folder

## 0.1.3 (2021-09-10)
