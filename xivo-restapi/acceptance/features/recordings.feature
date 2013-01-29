Feature: Call recordings management

	In order to create, consult and delete call recordings

	Scenario: Recording creation exception
	  Given there is no campaign
	  Given there is a queue named "test_queue"
	  Given there is a campaign named "test_campaign" for a queue "test_queue"
	  Given there is no agent with number "1111"
	  When I save call details for a call referenced by its "callid" in campaign "test_campaign" replied by agent with number "1111"
	  Then I get a response with error code '400' and message 'SQL Error: No such agent'

	Scenario: Recording creation and consultation
	  Given there is no campaign
	  Given there is a queue named "test_queue"
	  Given there is a campaign named "test_campaign" for a queue "test_queue"
	  Given there is an agent with number "1111"
	  When I save call details for a call referenced by its "callid" in campaign "test_campaign" replied by agent with number "1111"
	  Then I can consult these details
	  Then I delete this recording and the agent "1111"

	Scenario: Recording consultation and removing
	  Given there is no campaign
	  Given there is a queue named "test_queue"
	  Given there is a campaign named "test_campaign" for a queue "test_queue"
	  Given there is an agent of number "222"
	  Given there is a recording referenced by a "callid" with agent "222"
	  When I delete a recording referenced by this "callid"
	  Then the recording is deleted and I get a response with code "200"


	Scenario: Deleting of unexisting recording
	  Given there is no campaign
	  Given there is a queue named "test_queue"
	  Given there is a campaign named "test_campaign" for a queue "test_queue"
	  Given there is no recording referenced by a "callid" in campaign "test_campaign"
	  When I delete a recording referenced by this "callid"
	  Then I get a response with error code '404' with message 'No such recording'
	  

	Scenario: Recording search
	  Given there is no campaign
	  Given there is a campaign of id "1"
	  Given there is an agent "222"
	  Given there is an agent "111"
	  Given there is an agent "123"
	  Given I create a recording for campaign "1" with caller "111" and agent "222"
	  Given I create a recording for campaign "1" with caller "222" and agent "111"
	  Given I create a recording for campaign "1" with caller "123" and agent "123"
	  When I search recordings in the campaign "1" with the key "111"
	  Then I get the first two recordings
	  
	Scenario: Consistent number of recordings
	  Given there is no campaign
	  Given there is a campaign of id "1"
	  Given there is an agent "222"
	  Given there are at least "10" recordings for "1" and agent "222"
	  When I ask for the recordings of "1"
	  Then the displayed total is equal to the actual number of recordings
	  
	Scenario: Recording pagination
	  Given there is no campaign
	  Given there is a campaign of id "1"
	  Given there is an agent "222"
	  Given there are at least "10" recordings for "1" and agent "222"
	  When I ask for a list of recordings for "1" with page "1" and page size "5"
	  Then I get exactly "5" recordings
	  
	Scenario: No overlapping when paginating recordings
	  Given there is no campaign
	  Given there is a campaign of id "1"
	  Given there is an agent "222"
	  Given there are at least "10" recordings for "1" and agent "222"
	  Given I ask for a list of recordings for "1" with page "1" and page size "5"
	  Given I ask for a list of recordings for "1" with page "2" and page size "5"
	  Then the two lists of recording do not overlap
	
	Scenario: Pagination of search result
	  Given there is no campaign
	  Given there is a campaign of id "1"
	  Given there is an agent "222"
	  Given there are at least "10" recordings for "1" and agent "222"
	  When we search recordings in the campaign "1" with the key "222", page "2" and page size "5"
	  Then I get exactly "5" recordings
	  
	Scenario: Add recording end time
	  Given there is no campaign
	  Given there is a queue named "test_queue"
	  Given there is a campaign named "test_campaign" for a queue "test_queue"
	  Given there is an agent "222"
	  Given there is a recording in campaign "test_campaign" referenced by a "callid" answered by agent "222"
	  Given I update the recording referenced by a "callid" with end time "2099-01-13 10:25:55"
	  When I consult the recording referenced by a "callid"
	  Then I get a recording with end time "2099-01-13 10:25:55"
	  