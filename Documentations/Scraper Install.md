### Include:   
    - Environment variables
    - Git repository
    - Python packages
    - MongoDB
    - Ufw
	- Supervisor
    
### Install Process:
	- Phase 1: Update the packages list and install the prerequisites
	- Phase 2: update python \ git
	- Phase 3: MongoDB
	- Phase 4: Ufw
	- Phase 5: Environment variables
	- Phase 6: Project installation
	- Phase 7: Supervisor installation

### Phase 1:  
	- sudo apt-get update
	- sudo apt-get upgrade
	- sudo apt install software-properties-common
	- sudo add-apt-repository ppa:deadsnakes/ppa
	
### Phase 2:  
	- sudo apt install python3.9
	- sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 2
		sudo apt remove python3-apt
		sudo apt install python3-apt
	- sudo apt install python3-pip
	- sudo apt install python3-venv
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
	  echo "mongodb-org-server hold" | sudo dpkg --set-selections
      echo "mongodb-org-shell hold" | sudo dpkg --set-selections
      echo "mongodb-org-mongos hold" | sudo dpkg --set-selections
      echo "mongodb-org-tools hold" | sudo dpkg --set-selections
	- sudo reboot now
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
	- sudo nano /etc/environment
		look at the seprate file if you have access
    - sudo nano ~/.bashrc
        - alias agi='sudo apt-get install'
        - alias python='python3'
        - alias pip='pip3'

    
### Phase 6:  
    - git clone https://github.com/liron7722/SportPredictions
	- cd SportPredictions
	- git checkout --track origin/development
	- python3 -m venv venv
	- pip3 install -r Requirements/scraper_requirements.txt
	- sudo reboot now 


### Phase 7:  
    - sudo apt install supervisor
	- sudo mkdir -p /var/log/scraper/
	- sudo touch /var/log/scraper/monitor.err.log
	- sudo touch /var/log/scraper/monitor.out.log
	- sudo nano /etc/supervisor/conf.d/monitor.conf
		[program:ScraperMonitor]
		directory=/home/ubuntu/SportPredictions/
		command=python3 /home/ubuntu/SportPredictions/main.py 1
		user=ubuntu
		autostart=true
		autorestart=true
		stopasgroup=true
		killasgroup=true
		stderr_logfile=/var/log/scraper/monitor.err.log
		stdout_logfile=/var/log/scraper/monitor.out.log
	- sudo supervisorctl reload


	### Phase 8:  
		- ssh-keygen -t rsa -b 4096 -C "revahliron@gmail.com"
			press enter twice
		- ssh-copy-id remote_username@server_ip_address