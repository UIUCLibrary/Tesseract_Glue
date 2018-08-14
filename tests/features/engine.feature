# Created by hborcher at 8/13/2018
Feature: Engine
  Context class object that contains the context for OCR

  Scenario: Uses an engine to read the data
    Given a directory contains the english tesseract data
    And an engine is created
    And a directory contains an image containing english text
    Then the engine has version information
    And the engine can produce a reader object can get the text from the image