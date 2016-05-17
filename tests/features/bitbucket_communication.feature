Feature: Bitbucket communication
  In order to work effectively,
  As a developer,
  This resource should correctly update my Bitbucket server

Scenario: Accessing Bitbucket with bad credentials
    Given I used incorrect credentials to access Bitbucket
    Then I should get a 401 response and an error message

Scenario: Accessing Bitbucket with a repo my user doesn't have rights for
    Given I'm trying to update the status of a repo I don't have rights to
    Then I should get a 403 response and an error message

Scenario: Updating a build successfully
    Given I have configured this resource correctly
    Then I should get a 204 response
