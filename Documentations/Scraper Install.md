### Include:   
    - Environment variables
    - Git repository
    - Python packages
    - MongoDB
    - Ufw
    
### Install Process:
	- Phase 1: Update the packages list and install the prerequisites
	- Phase 2: update python \ git
	- Phase 3: MongoDB
	- Phase 4: Ufw
	- Phase 5: Environment variables
	- Phase 6: Project installation

### Phase 1:  
	- sudo apt-get update
	- sudo apt-get upgrade
	- sudo apt install software-properties-common
	- sudo add-apt-repository ppa:deadsnakes/ppa
	
### Phase 2:  
	- sudo apt install python3.9
	- sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 1
	- sudo apt install python3-pip
	- git config --global user.name liron7722
    - git config --global user.email liron7722@gmail.com
	
### Phase 3:  
	- wget -qO - https://www.mongodb.org/static/pgp/server-4.4.asc | sudo apt-key add -
	- sudo apt-get install gnupg
	- wget -qO - https://www.mongodb.org/static/pgp/server-4.4.asc | sudo apt-key add -
	- echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/4.4 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-4.4.list
	- sudo apt-get update
	- sudo apt-get install -y mongodb-org
	- echo "mongodb-org hold" | sudo dpkg --set-selections
    - echo "mongodb-org-server hold" | sudo dpkg --set-selections
    - echo "mongodb-org-shell hold" | sudo dpkg --set-selections
    - echo "mongodb-org-mongos hold" | sudo dpkg --set-selections
    - echo "mongodb-org-tools hold" | sudo dpkg --set-selections
	- (optional?) system reboot
	- sudo systemctl start mongod
	- sudo systemctl daemon-reload
	- sudo systemctl status mongod (press q to exit)
	- sudo systemctl enable mongod
	
### Phase 4:  
    - sudo apt-get install ufw
    - sudo ufw allow ssh
    - sudo ufw allow http
    - sudo ufw allow https
    - sudo ufw allow 27017
    - sudo ufw enable
	
### Phase 5:  
    - look at the seprate file if you have access
    - sudo nano ~/.bashrc
        - alias agi='sudo apt-get install'
        - alias python='python3'
        - alias pip='pip3'

    
### Phase 6:  
    - git clone https://github.com/liron7722/SportPredictions
	- cd SportPredictions
	- git checkout --track origin/development
	- pip3 install -r Requirements\scraper_requirements.txt
	- system reboot 