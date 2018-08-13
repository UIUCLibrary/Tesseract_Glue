# Created by hborcher at 8/13/2018
Feature: Engine
  Context class object that contains the context for OCR

  Scenario: Uses an engine to read the data
    Given a directory contains the english tesseract data
    And a directory contains an image containing english text
    And an engine creates a reader object with the eng lang code
    Then the reader object can get the text from the image