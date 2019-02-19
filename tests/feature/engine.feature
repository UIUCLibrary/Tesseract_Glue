# Created by hborcher at 8/13/2018
Feature: Engine
  Context class object that contains the context for OCR

  Scenario: Uses an engine to read the data
    Given a directory contains the english tesseract data
    And a directory contains an image containing english text
    And an engine is created
#    When the engine has version information
    When a reader is created
    Then the engine can produce a reader object can get the text from the image

