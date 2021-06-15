Feature: Latest episode
  Scenario Outline: Getting latest episodes of all configured podcasts
    Given an English speaking user
     When the user says "<new episodes>"
     Then "podcast-skill" should reply with dialog from "latestEpisodes.dialog"

  Examples: new episodes
    | new episodes |
    | check for new episodes |
    | latest episodes |
    | new episodes |

  Scenario Outline: Getting latest episode of specific podcast
    Given an English speaking user
     When the user says "newest episode of <existing podcast> podcast"
     Then "podcast-skill" should reply with dialog from "latestEpisode.dialog"

  Examples: existing podcast
    | existing podcast |
    | linux unplugged |
    | security now |
    | happier |

  Scenario: Getting latest episode of non existing podcast
    Given an English speaking user
     When the user says "newest episode of non existing podcast"
     Then "podcast-skill" should reply with dialog from "nopodcastfound.dialog"