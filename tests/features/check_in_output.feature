Feature: Validation of "check"/"in" results
  As a developer,
  Since this resource only supports output,
  In order to comply with the Concourse spec,
  Those two scripts must return empty data.

  Scenario: "In" call
    Given I have used the "in" script
    Then I should get back an empty JSON doc

  Scenario: "Check" call
    Given I have used the "check" script
    Then I should get back an empty array

