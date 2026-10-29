"""Generate PyInstaller version resource files for executables."""

from pathlib import Path


def generate_version_file(
    output_path: Path,
    original_filename: str,
    file_description: str,
    version_str: str = "1.2.0.0",
    product_name: str = "PinNotes",
    company_name: str = "kun",
    copyright_str: str = "Copyright (C) 2026 kun. All rights reserved.",
) -> Path:
    """Generate a PyInstaller VSVersionInfo text file."""
    parts = [int(p) for p in version_str.split(".")]
    while len(parts) < 4:
        parts.append(0)
    ver_tuple = tuple(parts[:4])

    content = f"""# UTF-8
#
# Windows PE Version Resource
#
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers={ver_tuple},
    prodvers={ver_tuple},
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        '040904B0',
        [StringStruct('CompanyName', '{company_name}'),
        StringStruct('FileDescription', '{file_description}'),
        StringStruct('FileVersion', '{version_str}'),
        StringStruct('InternalName', '{original_filename}'),
        StringStruct('LegalCopyright', '{copyright_str}'),
        StringStruct('OriginalFilename', '{original_filename}'),
        StringStruct('ProductName', '{product_name}'),
        StringStruct('ProductVersion', '{version_str}')])
      ]), 
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""
    output_path = Path(output_path)
    output_path.write_text(content, encoding="utf-8")
    return output_path
