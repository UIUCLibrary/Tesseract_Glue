import ocr
import types


def test_import_module():
    assert isinstance(ocr, types.ModuleType)


def test_engine(tessdata_eng):
    engine = ocr.Engine(data_set_path=tessdata_eng)
    reader = engine.get_reader(lang="eng")
    assert isinstance(reader, ocr.reader.AbsReader)
