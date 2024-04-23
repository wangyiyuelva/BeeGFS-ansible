# Distributed System for Large Scaled Data Analysis

## **About**

This is a distributed data analysis service across cloud machines. The nodes in this system are able to parallelly execute data analysis tasks in a pipeline structure. This pipeline consists of PytorchWildlife, pre-trained models tailored for animal detection, and Deeplabcut, a pre-trained animal pose estimation model. This service uses Ansible as a Configuration Management Tool, BeeGFS as a Parallel File System, RabbitMQ as a Message Queue, Prometheus for Monitoring, and Flask for the User Interface. Users can utilize the pipeline for analysis, track pipeline progress, and retrieve analysis outputs. This document describes the process of building this distributed data analysis service.

## System Architecture

![Untitled](https://prod-files-secure.s3.us-west-2.amazonaws.com/758ed74c-9864-49fb-a6b8-669c08225a5d/fb82562a-0f34-46a6-91fa-5792c0517381/Untitled.png)

## Requirement

- Hardware: 6 Linux servers (within same security group)
    - My case:
        - OS: Red Hat Enterprise Linux 9.3
        - Kernel: Linux 5.14.0-284.11.1.el9_2.x86_64
        - Host machine: smallest instance
        - Cluster Head machine:
            - 2 CPU Core and 2 Threads per Core
            - 200 GB disk
        - 4 Cluster Worker machines:
            - 1 CPU Core and 2 Threads per Core
            - 100 GB disk
- Software:
    - Python3

## **Environment Setup**

### Ansible

To manage the cluster, the Host should have Ansible.

```bash
sudo dnf install python3-pip
# on host
pip install ansible
# check if ansible is available
ansible --version
```

**Choice 1: Make your own ansible directory.**
Add the Cluster nodes' IP addresses to the inventory file so that the Host can control them.

```bash
mkdir ansible && cd ansible
vi inventory.yaml
# add all your machines' ip. See example `./ansible/inventory.yaml`
```

**Choice 2: Clone this repository to Host. All configure files are in `./ansible`**
Use the command to run all playbooks:

```bash
ansible-playbook --private-key=~/.ssh/{key-name} -i inventory.yaml {playbook-name}.yml
```

---

### **Mount Filesystem**

Attach a disk with enough capacity to the file system.

- Run `./ansible/mountDisk.yaml`
    - `mountDisk.yaml`: For every C**luster Nodes**, create a directory that will act as the mount point, formatting the device, and then binding the filesystem to that mount point.

---

### Configure Parallel File System — BeeGFS

1. Make authfile (or use `connauthfile` in `./ansible`)
    
    ```bash
    cd ansible
    dd if=/dev/random of=connauthfile bs=128 count=1
    ```
    
2. Install all packages 
    - Run `./ansible/beegfs_package.yml`
        - `beegfs_package.yml`: On **all nodes**, install all packages. Update packages takes a long while.
3. Configure Host
    - Run `./ansible/beegfs_host.yml`
        - `beegfs_host.yml`: On **Host**, configure metadata service and management service.
4. Configure Storage
    - Run `./ansible/beegfs_storage.yml`
        - `beegfs_storage.yml`: On **all Cluster Nodes**, configure storage service.
5. Configure BeeGFS client service 
    - Run `./ansible/beegfs_common.yml`
        - `beegfs_common.yml`: On **all nodes**, configure helperd service and client service
6. Now you have a shared file-system in `/beegfs`
    
    ```bash
    # check all node
    beegfs-ctl --listnodes --nodetype=meta
    # Will show Host
    # ip-{host-ip}.eu-west-2.compute.internal [ID: 1]
    beegfs-ctl --listnodes --nodetype=storage
    # Will show all cluster nodes
    # ip-{cluster-node-ip}.eu-west-2.compute.internal [ID: 1]
    # ip-{cluster-node-ip}.eu-west-2.compute.internal [ID: 2]
    # ip-{cluster-node-ip}.eu-west-2.compute.internal [ID: 3]
    # ip-{cluster-node-ip}.eu-west-2.compute.internal [ID: 4]
    # ip-{cluster-node-ip}.eu-west-2.compute.internal [ID: 5]
    ```
    
7. Add directories for data
    
    ```bash
    mkdir /beegfs/data
    mkdir /beegfs/data/input
    mkdir /beegfs/data/input_done
    mkdir /beegfs/data/output
    # You can use scp to upload dataset into /beegfs/data/input.
    # After data processing, old input will be stored in /beegfs/data/input_done
    # Output will be in /beegfs/data/output
    ```
    

---

### Install Packages

The pipeline require these dependencies

1. pip
2. mesa-libGL (in RHEL ****OS)
3. PytorchWildlife
4. Deeplabcut
- Run `./ansible/install_tool.yml`
    - `install_tool.yml`: Install all yum packages and virtualenv
- Run `./ansible/packages_for_pipeline.yml`
    - `packages_for_pipeline.yml`: Install PytorchWildlife and deeplabcut in virtualenv
- Install this repository into shared filesystem
    
    ```bash
    cd /beegfs
    git clone ... pipeline
    ```
    

---

### Configure Message Queue — RabbitMQ

1. Configure RabbitMQ server
    - Run `./ansible/rabbitmq_setting.yml`
        - `rabbitmq_setting.yml`: On Cluster Head, setting rabbitMQ server.
2. Install pika: Implementation of the AMQP 0-9-1 protocol including RabbitMQ's extensions.
    - Run `./ansible/install_pika.yml`
        - `install_pika.yml`: install pika in virtualenv

---

### Configure Monitoring — **Prometheus**

As a manager of the cluster, the Host should have Prometheus.

- Run `./ansible/prometheus_setup.yml`
    - I have downloaded prometheus-2.45.4 and node_exporter-1.7.0 in this repository, just use ansible to tar them.
    - you can download it by yourself via: https://prometheus.io/download/
- Adjust the configuration file (`prometheus.yml`) by adding the IP addresses of all 5 cluster nodes to the targets.

```yaml
cd /beegfs/prometheus/prometheus-2.45.4/
# prometheus.yml
- job_name: "prometheus"

    # metrics_path defaults to '/metrics'
    # scheme defaults to 'http'.

    static_configs:
      - targets: ["localhost:9090"]
- job_name: "node"
    static_configs:
      - targets: ['10.0.0.108:9100']
      - targets: ['10.0.5.211:9100']
      - targets: ['10.0.2.25:9100']
      - targets: ['10.0.6.86:9100']
      - targets: ['10.0.0.75:9100']
```

- run Prometheus:

```bash
./prometheus --web.enable-admin-api --config.file=prometheus.yml
```

Now you can see the Prometheus UI on the browser: `http://{Host IP public addr}:9090`

**Node exporter**

- Run `./ansible/node_exporter.yml`
    - On each Cluster node, run the exporter in the background so that we can observe the states of each node on Prometheus at any time.

**During node running**

- Use Prometheus to monitor the state and CPU load on each node.
    
    ```sql
    # PromQL
    (sum by (instance) (rate(node_cpu_seconds_total{mode!="idle"}[3m])) * 100)
    ```
    

---

### Running Pipeline

1. Input data for processing should be in your shared filesystem. You can use `scp` to transfer the dataset into `/beegfs/data/input`, which is the target directory the producer looks at.
    - Benchmark: [Dataset](https://drive.google.com/drive/folders/147a6sJQ0RTduiVsLp8LyF0I4xE4PFXGl?usp=sharing) (with input and output)
        - You can download it and `scp` it into `/beegfs/data/input`
    - All videos should be in MP4 format and directly placed in `/beegfs/data/input`, not in a subdirectory.
2. Publishing messages by producer :
    - Run `./ansible/run_producer.yml`
        - `run_producer.yml`: Use **Cluster Head** to run `./rabbitmq/producer.py`, which puts all target tasks into message queue.
3. Receiving messages by consumers:
    - Run `./ansible/run_consumer.yml`
        - `run_consumer.yml`: Use **all Cluster Nodes** to run `rabbitmq/consumer_run_pipeline.py` in the background. Receive target tasks from the message queue and execute the data processing pipeline.
    - You can monitor all message queues, channels, and the runtime process by accessing RabbitMQ Management Panel
        - `http://{Cluster-Head-public-ip}:15672`
    - If `./ansible/run_consumer.yml` doesn’t work, manually run `nohup /beegfs/pipeline/runConsumer.sh &` on **all Cluster Nodes.**
    - Check that everything is running by using the RabbitMQ Management Panel or monitoring all nodes through the Prometheus UI.
4. All output will be stored in `/beegfs/data/output` .  Output video name should be `{input-filename}wildDLC_snapshot-700000_labeled.mp4`. Output plots should be in `/beegfs/data/output/plot-poses/BZAGTQTXwild`

---

## Running New data

### Approach 1: Upload from Web UI

1. Choose one node to build webapp(Suggest Cluster Head, or Host)
    
    ```bash
    # on cluster head
    source /beegfs/virtualenv/venv/bin/activate
    # install web package
    pip install Flask gunicorn
    # use nginx for port forwarding
    sudi yum install nginx
    sudo systemctl enable nginx
    sudo systemctl start nginx
    curl {public ip} # check connect
    ```
    
2. Setting Nginx
    1. Approach 1
        
        ```bash
        sudo vi /etc/nginx/conf.d/app.conf
        # add this
        server {
            listen 80;
            server_name 18.171.237.27;  # here should be modified to your IP
        
            location / {
                proxy_pass http://127.0.0.1:8000;
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
                client_max_body_size 5M;
            }
        }
        # restart nginx
        sudo systemctl restart nginx
        setsebool httpd_can_network_connect on
        ```
        
    2. Approach 2
        
        ```bash
        sudo vi /etc/nginx/sites-available/myapp
        ```
        
        ```
        # add this
        server {
            listen 80;
            server_name 18.171.237.27;  # here should be modified to your IP
        
            location / {
                proxy_pass http://127.0.0.1:8000;
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
                client_max_body_size 5M;
            }
        }
        ```
        
        If `/etc/nginx/sites-available/` folder not found
        
        ```bash
        sudo mkdir /etc/nginx/sites-available
        sudo mkdir /etc/nginx/sites-enabled
        sudo vi /etc/nginx/sites-available/myapp # add the same server as above
        # edit the http block inside /etc/nginx/nginx.conf and add this line:
        include /etc/nginx/sites-enabled/*;
        # set Symbolic link
        sudo ln -s /etc/nginx/sites-available/myapp /etc/nginx/sites-enabled/myapp
        
        # restart nginx
        sudo systemctl restart nginx
        setsebool httpd_can_network_connect on
        ```
        
3. Run Webapp
    
    ```bash
    source /beegfs/virtualenv/venv/bin/activate
    cd /beegfs/pipeline/flask/
    gunicorn app:app
    # You can access webUI via http://{public ip}. 
    # Upload a video that is smaller than 5MB.
    ```
    
4. Publishing messages by producer :
    - In Host: Run `./ansible/run_producer.yml`
5. Access Output
    - You can access the page: `http://{public ip}/Log` to monitor progress.
    - If the process is complete,  you can download the output video via the page: `http://{public ip}/output/filename`
        - For example, your uploaded video is abc.mp4, then download it via: `http://{public ip}/output/abc`
    - You can download the output plot via the page: `http://{public ip}/plot/filename`
        - For example, your uploaded video is abc.mp4, then download it via: `http://{public ip}/plot/abc`
6. Test Examples (TODO: add example)
    - You can test this by examples: `./flask/example/input`
    - example outputs are in `./flask/example/output`

### Approach 2: Upload by `scp`

1. Use `scp` to copy your dataset into `/beegfs/data/input`
    - All videos should be in MP4 format and directly placed in `/beegfs/data/input`, not in a subdirectory.
2. Publishing messages by producer :
    - In Host: Run `./ansible/run_producer.yml`
3. Monitoring progress 
    - Node runtime status: Prometheus `http://{Host IP public addr}:9090`
    - All tasks progress, consumers runtime status: RabbitMQ `http://{Cluster-Head-public-ip}:15672.`
    - Each Video Process: WebUI `http://{web public ip}/Log`
4. Use `scp` to copy all output from `/beegfs/data/output`