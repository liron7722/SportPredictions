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
	- Phase 4: NPM
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
	- sudo apt install python3-pip
	- sudo apt install python3-venv
	- git config --global user.name liron7722
    - git config --global user.email liron7722@gmail.com

### Phase 3:  
	- sudo apt install npm
	- sudo npm install pm2@latest -g
	- pm2 -v
	- pm2 start main.py 1 --name soccer_scraper --interpreter python3

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
