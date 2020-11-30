### Known Bugs:   
    - Memory (Ram) Overflow?
    - You tell me
    
### Coming  Up:
    - Save ram memory - Make db upload after every season scrape and then delete it from memory
	- Check db download
	- check loop scrape work as intended
	- Complete season test file
	- Project name + env_type - Environment variables

### ToDo List:  
	- ELK 
	- Environment variables
	- Docker
    - Files struture check up
	- Data analysis
	- Add ML: sklearn, pytourc, TensorFlow, Keras
	- Move to cloud (aws) (Instanse for ELK \ DB \ Scraper \ Data analysis \ ML Modeling Separtly)
	- Auto restart
	- Monitor
	- Website
	- Added more sports
	    - Complete {Sport} Scraper
	    - Data analysis
	    - ML
	    - Move to cloud


### Updates:
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
	