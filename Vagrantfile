Vagrant.configure("2") do |config|
  config.vm.box = "minimal/xenial64"
  config.vm.provider "virtualbox" do |vb|
    vb.memory = "3000"  
  end
  config.vm.provision "shell", path: "install-deps.sh"
  config.vm.provision "file", source: "dirlist.py", destination: "/home/vagrant/dirlist.py"
end
