Feature: Latest episode
  Scenario: Getting latest episodes
    Given an English speaking user
     When the user says "check for new episodes"
     Then "podcast-skill" should reply with dialog from "latest.dialog"