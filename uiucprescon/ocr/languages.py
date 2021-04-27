"""This contains everything related to the language data files."""
import os
import zipfile
from urllib import request
import tempfile
import hashlib
import time

LANGUAGE_CODES = {
    "afr": "Afrikaans",
    "amh": "Amharic",
    "ara": "Arabic",
    "asm": "Assamese",
    "aze": "Azerbaijani",
    "aze_cyrl": "Azerbaijani - Cyrilic",
    "bel": "Belarusian",
    "ben": "Bengali",
    "bod": "Tibetan",
    "bos": "Bosnian",
    "bre": "Breton",
    "bul": "Bulgarian",
    "cat": "Catalan; Valencian",
    "ceb": "Cebuano",
    "ces": "Czech",
    "chi_sim": "Chinese - Simplified",
    "chi_tra": "Chinese - Traditional",
    "chr": "Cherokee",
    "cym": "Welsh",
    "dan": "Danish",
    "deu": "German",
    "dzo": "Dzongkha",
    "ell": "Greek, Modern (1453-)",
    "eng": "English",
    "enm": "English, Middle 1100-1500",
    "epo": "Esperanto",
    "equ": "Math / equation detection module",
    "est": "Estonian",
    "eus": "Basque",
    "fas": "Persian",
    "fin": "Finnish",
    "fra": "French",
    "frk": "Frankish",
    "frm": "French Middle (ca.1400-1600)",
    "gle": "Irish",
    "glg": "Galician",
    "grc": "Greek, Ancient (to 1453)",
    "guj": "Gujarati",
    "hat": "Haitian; Haitian Creole",
    "heb": "Hebrew",
    "hin": "Hindi",
    "hrv": "Croatian",
    "hun": "Hungarian",
    "iku": "Inuktitut",
    "ind": "Indonesian",
    "isl": "Icelandic",
    "ita": "Italian",
    "ita_old": "Italian - Old",
    "jav": "Javanese",
    "jpn": "Japanese",
    "kan": "Kannada",
    "kat": "Georgian",
    "kat_old": "Georgian - Old",
    "kaz": "Kazakh",
    "khm": "Central Khmer",
    "kir": "Kirghiz; Kyrgyz",
    "kor": "Korean",
    "kor_vert": "Korean vertical",
    "kur": "Kurdish",
    "kur_ara": "Kurdish Arabic",
    "lao": "Lao",
    "lat": "Latin",
    "lav": "Latvian",
    "lit": "Lithuanian",
    "ltz": "Luxembourgish",
    "mal": "Malayalam",
    "mar": "Marathi",
    "mkd": "Macedonian",
    "mlt": "Maltese",
    "mon": "Mongolian",
    "mri": "Maori",
    "msa": "Malay",
    "mya": "Burmese",
    "nep": "Nepali",
    "nld": "Dutch; Flemish",
    "nor": "Norwegian",
    "oci": "Occitan post 1500",
    "ori": "Oriya",
    "osd": "Orientation and script detection module",
    "pan": "Panjabi; Punjabi",
    "pol": "Polish",
    "por": "Portuguese",
    "pus": "Pushto; Pashto",
    "que": "Quechua",
    "ron": "Romanian; Moldavian; Moldovan",
    "rus": "Russian",
    "san": "Sanskrit",
    "sin": "Sinhala; Sinhalese",
    "slk": "Slovak",
    "slv": "Slovenian",
    "snd": "Sindhi",
    "spa": "Spanish; Castilian",
    "spa_old": "Spanish; Castilian - Old",
    "sqi": "Albanian",
    "srp": "Serbian",
    "srp_latn": "Serbian - Latin",
    "sun": "Sundanese",
    "swa": "Swahili",
    "swe": "Swedish",
    "syr": "Syriac",
    "tam": "Tamil",
    "tat": "Tatar",
    "tel": "Telugu",
    "tgk": "Tajik",
    "tgl": "Tagalog",
    "tha": "Thai",
    "tir": "Tigrinya",
    "ton": "Tonga",
    "tur": "Turkish",
    "uig": "Uighur; Uyghur",
    "ukr": "Ukrainian",
    "urd": "Urdu",
    "uzb": "Uzbek",
    "uzb_cyrl": "Uzbek - Cyrilic",
    "vie": "Vietnamese",
    "yid": "Yiddish",
    "yor": "Yoruba",
}  #: The codes used by Tesseract for a specific languages data set


def _download_languague(url: str,
                        destination: str,
                        md5_hash: str = None) -> str:

    block_size = 16 * 1024
    base_name = os.path.basename(url)
    destination_file = os.path.join(destination, base_name)

    if os.path.exists(destination_file):
        if not md5_hash:
            return destination_file
        hash_data = hashlib.md5()
        with open(destination_file, "rb") as file_reader:
            buffer = file_reader.read(block_size)
            while len(buffer) > 0:
                hash_data.update(buffer)
                buffer = file_reader.read(block_size)
        if hash_data.hexdigest() == md5_hash:
            return destination_file
    file_pointer, temp_file = tempfile.mkstemp(dir=destination)
    try:
        with os.fdopen(file_pointer, "wb") as file_writer:
            response = request.urlopen(url)
            i = 0
            hash_data = hashlib.md5()
            start_time = time.time()
            last_printed = start_time
            while True:
                chunk = response.read(block_size)
                if not chunk:

                    break
                file_writer.write(chunk)
                hash_data.update(chunk)
                i += 1
                update_time = time.time()
                if update_time - last_printed > 0.5:
                    last_printed = time.time()
                    print("Download Tesseract language data"
                          ": {:.2f} MB".format(file_writer.tell() / 1e+6))

            if md5_hash is not None and hash_data.hexdigest() != md5_hash:
                raise IOError("File does not match expected hash")

            print("Downloaded Tesseract language data. "
                  "Total {:.2f} MB".format(file_writer.tell() / 1e+6))

        print("Renaming {} to {}".format(temp_file, destination_file))
        os.rename(temp_file, destination_file)
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)
    return destination_file


def download_language_pack(tesseract_version: str, destination: str,
                           md5_hash: str = None) -> None:
    """Download a specific version of Tesseract training data.

        Args:
            tesseract_version: Version of Tesseract used.
            destination: Path to save the language data
            md5_hash (optional): Expected md5 hash value of the
                downloaded archive. If file is already downloaded, it
                will not need to be downloaded again.

    """
    base_url = "https://codeload.github.com/tesseract-ocr/tessdata/zip"

    url = "{}/{}".format(base_url, tesseract_version)
    language_pack_archive = _download_languague(url, destination, md5_hash)
    _extract_language_pack(language_pack_archive, destination)


def _extract_language_pack(language_pack: str, destination: str) -> None:
    with zipfile.ZipFile(language_pack) as archive:
        for compressed_file in archive.namelist():
            print("Extracting {}".format(compressed_file))
            archive.extract(compressed_file, destination)
