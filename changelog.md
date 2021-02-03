### Known Bugs:
    - You tell me
    
### Coming  Up:
    - fix test script of season after json string to json update
    - fix match_fixture and season test files after changes
    - add data handler test file    
    
    - check read past season data properly
    - check calculated fixture data save properly - look at past season

### ToDo List: 
    - Better logger for api

    - Data handling
        - Handle players data

    - Data analysis
        - Auto Analayzers per column to predict

	- Add ML: sklearn, pytourc, TensorFlow, Keras
        - Make more models
        - check for cloud solutions

	- Website with on demend predictions
        - UI
        - Donate Option
        - Upcoming and Archive of fixture predictions
        - User management
        - Payment method for checking predictions
        

	- Added more sports
	    - NFL (Football)
        - NBA (Basketball)
        - MLB (Baseball)
        - NHL (Hockey)
        
    - Miscellaneous
	    - ELK for logs
	    - Dockers for each project part
        - Files struture check up
	    - Move to cloud (aws) (Instanse for ELK \ Data analysis \ ML Modeling Separtly)
	    - Auto restart
	    - Monitor

### Updates:
#### update 11#:
    - change api location
    - added new keys to predict
    - now data handler dont create all time stats for teams and managers
    - now data handler dont create extra time columns
    - Soccer screaper and DB now work on aws instanses
    - models drop null values in y make it more accurate
    - better db document search
    - data handler now add Head to Head stats from previus fixtures

#### update 10#:
    - added rfr predictor and predictor handler
    - added predictor api
    - added utility script: parallel
    - Preventing unnecessary model creation
    - dealing with null in predicion columns
    - handling when teams in fixture got Possession key with out value

#### update 9#:
    - added fixture, team, manager, referee data handler
    - added functions to utility scripts
    - added 2nd yellow card support
    - added version to match report and fixture handling
    - improved memory management
    - fixed a bug where wasn't saveing fixture stats properly if Possession wasn't on stats list
    - fixture dict table are now dict inside as well instead of json strings
    - now will download a season from start if we changed the season or match report version

#### update 8#:
    - bugs fix and small improvements
    - changed db save and upload structure
    - new files structure
    - added side info to events in match fixture

#### update 7#:
    - added support for python 3.8
    - reorganized the data in the mongoDB in order to not get files above 16MB
    - no longer download season data that was downloaded before
    - added logger to test scripts
    - changed classes static variables in order to avoid data leak between classes
    - match fixture bugs fix
    - minor improvements in utility scripts
    - added retry option when trying to get a url in case of a bad status code
    - json strings will now be jsons as well

#### update 6#: 
    - add basic.py to inherit by soccer scripts
    - improved code structure
    - add db save support for soccer scripts
    - Memory improvement - now save season after it been scraped instead of when it all finished
    - Fixed test scripts after changes
    - added Environment variables
    - Now scrape all of the competition seasons befor moving to the next competition
    - removed scraped flag
    - fixed an issue where scrape list of fixtures won't update properly

    
#### update 5#: 
    - added timer wrapper to time script
    - added timer logs at soccer scraper and competition scripts
    - added log error in competition script

#### update 4#: 
    - Documentions
	- Requirements File
	- Bug fix - added support for new head to head history links in fixrues list and in match reports
    - Bug fix - where Manager or Captian isn't listed
    - Bug fix - where match don't have match time in scorebox
    - Bug fix - where match report had only 2 tables on players stats
    - small improvement in match fixture score box scrape 

#### update 3#:  
    - added scraper scripts for competition and soccer scraper
    - added test scripts for competition and soccer scraper
    - added test files for competition
    - Complete Soccer Scraper
    - Main script
    - added utility script (time)
    - Integrate DB (MongoDB)
    - Integrate logger
    - added 2 more tests to season test
	- fixed bugs and minor improvements
	
    
#### update 2#:  
	- added Utility scripts like db, json, requests, logger
	- better files structure
	- added scraper scripts for matches and seasons
	- added test scripts for matches and seasons
	- added test files for matches and seasons

#### update 1#:  
	- init git  
	