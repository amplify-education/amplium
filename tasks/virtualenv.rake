namespace "virtualenv" do
  desc "Verify that we are running in a virtualenv"
  task :verify do
    sh 'python -c "import sys; sys.real_prefix" &>/dev/null' do |ok, status|
      ok or error(["Python virtualenv not activated",
                   "Create or activate a virtualenv to work on this egg."])
    end

    # unset PYTHONPATH if it is set
    warn("PYTHONPATH is set; unsetting it for safety") if ENV.delete('PYTHONPATH')

    notice("Verified we are running in a virtualenv")
  end

  desc "Create a virtualenv"
  task :create => [:destroy] do
    venv_dir = ProjectPaths::TEST_VIRTUALENV_DIR
    script = <<-EOS
    /bin/bash -c '
    if [ ! -z $(type -t deactivate) ]; then
      deactivate
    fi
    virtualenv #{venv_dir}
    '
    EOS
    sh script do |ok, status|
      ok or error("Failed to create a virtualenv")
    end
    notice "Created a virtualenv at #{venv_dir}"
  end

  desc "Destroy a virtualenv"
  task :destroy do
    venv_dir = ProjectPaths::TEST_VIRTUALENV_DIR
    if File::directory?(venv_dir)
      rm_rf venv_dir
      notice "Destroyed a virtualenv at #{venv_dir}"
    else
      notice "No virtualenv to destroy, moving along"
    end
  end
end

