Feature: Dropping the Fuego and FHIR EPR data

  Background:
    Given a valid JWT

  Scenario: Data drop
    Given a patient is present in EPR
    When I search for the patient by MRN
    Then I see the expected patient in search results
    When I perform data drop
    And I search for the patient by MRN
    Then I see no patients in search results
