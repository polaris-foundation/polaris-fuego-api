Feature: Searching EPR for patients
  As a clinician
  I want to be able to search for patients in EPR
  So that I don't have to double-enter data

  Background:
    Given a valid JWT

  Scenario: Search for an existing patient in EPR
    Given a patient is present in EPR
    When I search for the patient by MRN
    Then I see the expected patient in search results
