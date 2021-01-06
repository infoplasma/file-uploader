I have created a new VM instance on GCP, within bosch project, to deploy the app on the web

the VM instance name is `file-uploader`

to set up the VM with web server:
`gcloud compute --project "bosch-dashboard-295910" ssh --zone europe-west6-a file-uploader`

passphrase: `infoplasma`

this vm is a debian 9.

we need to install pip, and virtualenv first
then nginx and gunicorn
and settup firewall permissions

process
setupbasic firerwall

sudo apt update
apt install ufw

ufw app list
allow the following
(file-uploader) lorenzo_amante@file-uploader:~/dev/file-uploader$ sudo ufw status
Status: active

To                         Action      From
--                         ------      ----
Nginx HTTP                 ALLOW       Anywhere                  
SSH                        ALLOW       Anywhere                  
OpenSSH                    ALLOW       Anywhere                  
5000                       ALLOW       Anywhere                  
Nginx HTTP (v6)            ALLOW       Anywhere (v6)             
SSH (v6)                   ALLOW       Anywhere (v6)             
OpenSSH (v6)               ALLOW       Anywhere (v6)             
5000 (v6)                  ALLOW       Anywhere (v6)             
 
ufw enable

you can follow similar approach as Ubuntu:
https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-18-04

 python
    2  python3
    3  git
    4  apt get git
    5  apt install git
    6  sudoapt install git
    7  sudo apt install git
    8  ls -l
    9  mkdir dev/file-uploader
   10  mkdir dev
   11  ls -l
   12  cd dev
   13  mkdir file-uploader
   14  ls -l
   15  cd ..
   16  cd dev
   17  rmdir file-uploader/
   18  ls -l
   19  clear
   20  git clone
   21  git clone https://github.com/infoplasma/file-uploader.git
   22  ls -l
   23  cd file-uploader/
   24  ls -l
   25  cd ..
   26  apt-get install pip3
   27  sudo apt-get install pip3
   28  sudo apt-get install python3-pip
   29  sudo pip3 install virtualenv
   30  ls -l
   31  cd dev
   32  mkdir venvs
   33  cd venvs/
   34  virtualenv file-uploader
   35  cd ../file-uploader/
   36  ls -l
   37  source ../venvs/file-uploader/bin/activate
   38  ls -l
   39  pip3 install -r requirements.txt 
   40  ls -l
   41  python3 app.py 
   42  sudo python3 -m http.server 80
   43  sudo python3 -m app.py 80
   44  python3 -m app.py 5000
   45  python3 -m app.py
   46  python3 app.py
   47  ls
   48  cd logging/
   49  ls -l
   50  ls logfile.log 
   51  less logfile.log 
   52  vim app
   53  ls -l
   54  cd ..
   55  ls -l
   56  vim app.py 
   57  python3 app.py
   58  vim app.py 
   59  sudo apt-get install gunicorn
   60  sudo apt install nginx
   61  sudo vim /etc/nginx/sites-enabled/file-uploader
   62  less /etc/nginx/sites-enabled/default 
   63  sudo unlink /etc/nginx/sites-enabled/default 
   64  sudo nginx -s reload
   65  sudo vim /etc/nginx/sites-enabled/file-uploader
   66  sudo nginx -s reload
   67  gunicorn -w 3 file-uploader:app
   68  gunicorn -w 3 app.py 
   69  ufw
   70  sudo ufw app lis
   71  apt install ufw
   72  sudo apt install ufw
   73  sudo ufw app list
   74  sudo ufw allow 'Nginx HTTP'
   75  sudo ufw status
   76  ufw enable
   77  sudo ufw enable
   78  sudo ufw allow 'SSH'
   79  sudo ufw allow 'OpenSSH'
   80  sudo ufw enable
   81  sudo status
   82  sudo ufw status
   83  sudo ufw allow 5000
   84  sudo ufw status
   85  ls -l
   86  cd dev
   87  cd file-uploader/
   88  ls -l
   89  source ../venvs/file-uploader/bin/activate
   90  ls -l
   91  python3 app.py 
   92  cd logging/
   93  less logfile.log 
   94  cd ..
   95  less app.py 
   96  ls -l
   97  python3 
   98  less app.py 
   99  python3 app.py 
  100  history
 


I hhave set the max upload file size to 40M in ngnix config file `/etc/nginx/nginx.conf`:

        client_max_body_size 40M;

to reload nginx:

      sudo systemctl restart nginx
