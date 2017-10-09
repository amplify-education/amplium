require 'shellwords'

module Jenkins
  # We remember the Jenkins API key in a file named after the Jenkins URL
  # Before we supported configurable Jenkins URLs, we stored the API key in
  # a file ~/.jenkins_api_key. The read_api_key method attempts to make
  # this transition seamless.
  DEPRECATED_KEY_FILE = "#{ENV['HOME']}/.jenkins_api_key"

  KEY_FILE_DIR = "#{ENV['HOME']}/.jenkins_api_key.d"
  JOB_NAME_SUFFIX = {
    'BUILD' => '-BUILD',
    'CI-INTEGRATIONTEST' => 'ci-INTEGRATIONTEST',
    'QA-DEPLOY' => 'qa-DEPLOY'
  }
  CONFIG_TEMPLATE_PATH = {
    'BUILD' => 'jenkins/config-BUILD.xml.template',
    'CI-INTEGRATIONTEST' => 'jenkins/config-CI-INTEGRATIONTEST.xml.template',
    'QA-DEPLOY' => 'jenkins/config-QA-DEPLOY.xml.template'
  }
  CONFIG_PATH = {
    'BUILD' => 'jenkins/config-BUILD.xml',
    'CI-INTEGRATIONTEST' => 'jenkins/config-CI-INTEGRATIONTEST.xml',
    'QA-DEPLOY' => 'jenkins/config-QA-DEPLOY.xml'
  }

  @password = nil

  # Calculates a host-specific key file path
  def self.key_file_for_jenkins_url(jenkins_url=nil)
    jenkins_url ||= Project[:JENKINS_URL]
    filename = jenkins_url.gsub(/https?:\/\//, '').gsub(/[^A-Za-z0-9\.]/, '_')
    File.join(KEY_FILE_DIR, filename)
  end

  def self.read_api_key
    # If the host-specific file exists, we read that.
    #
    # If it doesn't, check for the deprecated key file. If that exists AND this project's JENKINS_URL
    # is the default, then that's probably the right key, so we copy that to a host-specific file.
    #
    # Otherwise, fail.
    if File.exist?(key_file_for_jenkins_url) then
      File.read(key_file_for_jenkins_url)
    elsif File.exist?(DEPRECATED_KEY_FILE) and Project[:JENKINS_URL] == Project::DEFAULTS[:JENKINS_URL] then
        warn([
          "No host-specific Jenkins API key for #{Project[:JENKINS_URL]} was found",
          "But I did find an old key in #{DEPRECATED_KEY_FILE}, so copying from there"
        ])
        api_key = File.read(DEPRECATED_KEY_FILE)
        write_api_key(api_key)
        # Re-invoke this method, which should now find the key
        read_api_key
    else
      raise IOError.new("Couldn't find a Jenkins API key")
    end
  end

  def self.write_api_key(api_key)
    mkdir_p(KEY_FILE_DIR)
    File.chmod(0700, KEY_FILE_DIR)
    File.open(key_file_for_jenkins_url, 'w') do |f|
      f.write(api_key)
      puts "Wrote Jenkins API key to #{key_file_for_jenkins_url}"
    end
    # Make sure the API key is readable only by the user
    File.chmod(0600, key_file_for_jenkins_url)
  end

  def self.ask_api_key
    url = "#{Project[:JENKINS_URL]}/user/#{ENV['USER']}/configure"
    puts "Jenkins tasks require your Jenkins API key, which can be found on your Jenkins user page."
    puts "1. Open: #{url}"
    puts "2. Click \"Show API Token...\""
    puts "3. Copy the token"
    puts ""
    ask "Press return and I will try to open your user page for you:"
    browse(url)
    api_key = ask "Please paste your Jenkins API token here: "
    write_api_key(api_key)
    return read_api_key
  end

  def self.get_password
    if @password.nil?
      ask_password
    end
    return @password
  end

  def self.ask_password
    @password = ask_noecho("Enter your LDAP password for Jenkins: ")
  end

  def self.instantiate_config(config, opts={})
    #
    # This whole thing is a very poor man's templating.
    # Should really consider layering erb templates in here.
    #
    opts = default_opts(opts)
    git_origin = Git.get_origin
    instantiated = config.gsub(/\[PROJECT_GIT_REPO\]/, git_origin) 
    # Hostclass
    instantiated.gsub!(/\[PROJECT_HOSTCLASS\]/, Project[:HOSTCLASS] || "")
    # Github
    instantiated.gsub!(/\[GITHUB_URL\]/, Hub.get_github_project_url)
    # We might create jobs for different environments
    instantiated.gsub!(/\[JOB_ENVIRONMENT_UPCASE\]/, opts[:env].upcase)
    instantiated.gsub!(/\[JOB_ENVIRONMENT\]/, opts[:env])
    # Some special-casing when PROJECT_SUBDIR is ., 
    # because Jenkins doesn't understand that './foo.xml' is the same 
    # as just 'foo.xml'
    if Git.get_path_from_root == '.' then
      instantiated.gsub!(/\[PROJECT_SUBDIR\]\//, '')
    end
    instantiated.gsub!(/\[PROJECT_SUBDIR\]/, Git.get_path_from_root)
    instantiated
  end

  def self.create_config_xml(opts={})
    opts = default_opts(opts)
    template_path = CONFIG_TEMPLATE_PATH[opts[:task]] or raise("Couldn't find the template file for task: #{opts[:task]}")
    template = File.read(template_path)
    # substitute!
    instantiated = instantiate_config(template, opts)
    # write
    config_path = CONFIG_PATH[opts[:task]]
    File.open(config_path, 'w') do |f|
      f.write(instantiated)
    end
  end

  #
  # Create a Jenkins job with the specified options.
  # Returns the URL of the created job, or raises an exception on
  # failure.
  #
  def self.create_job(opts={})
    opts = default_opts(opts)
    name = job_name(opts)
    api_key = read_api_key
    pw = Jenkins.get_password
    config_file = Jenkins::CONFIG_PATH[opts[:task]]

    notice("Creating Jenkins job: #{name}")

    result = `curl --silent -k --user $USER:#{Shellwords.shellescape(pw)} -X POST -H 'Content-type: application/xml' --data @#{config_file} '#{Project[:JENKINS_URL]}/createItem?name=#{name}&token=#{api_key}'`
    status = $?
    error_match = result.match(/(?:<h1>Error<\/h1><p>)|(?:<h1\>Status Code:.\d+<\/h1>)(.+)(?:<\/p>|<br>)/)
    if status != 0 or error_match then
      error_msg = "#{error_match[1] if error_match}"
      status_msg = (status != 0) ? "(status #{status})" : ""
      msg = "#{error_msg} #{status_msg}"
      raise "Job creation failed. #{msg}"
    end
    Jenkins.job_url(opts)
  end

  def self.job_name(opts={})
    opts = default_opts(opts)
    suffix = JOB_NAME_SUFFIX[opts[:task]]
    "#{Project[:PROJECT]}-#{opts[:env]}#{suffix}"
  end

  def self.default_opts(opts={})
    opts = {:env => 'future', :task => 'BUILD'}.merge(opts)
    opts
  end

  def self.job_url(opts={})
    "#{Project[:JENKINS_URL]}/job/#{job_name(opts)}"
  end

end

namespace "jenkins" do
  desc "Create Jenkins jobs"
  task :create => [:create_build] do
    # If this is a component, create CI integration and QA deploy jobs
    if Project[:IS_COMPONENT]
      Rake::Task["jenkins:create_ci_integrationtest"].invoke
      Rake::Task["jenkins:create_qa_deploy"].invoke
    end
  end

  desc "Create Jenkins build job"
  task :create_build => [:apikey, :createxml_build] do
    opts = {
      :task => 'BUILD',
      :env => 'future'
    }
    url = Jenkins.create_job(opts)
    good("Build job created")
    puts "Build job URL: #{url}"
    browse(url)
  end

  desc "create jenkins CI integration test job"
  task :create_ci_integrationtest => [:apikey, :createxml_ci_integrationtest] do
    opts = {
      :task => 'CI-INTEGRATIONTEST',
      :env => 'future'
    }
    url = Jenkins.create_job(opts)
    good("integration test job created")
    puts "integration test job url: #{url}"
    browse(url)
  end

  desc "create jenkins QA deploy job"
  task :create_qa_deploy => [:apikey, :createxml_qa_deploy] do
    opts = {
      :task => 'QA-DEPLOY',
      :env => 'future'
    }
    url = Jenkins.create_job(opts)
    good("QA deploy job created")
    puts "QA deploy job url: #{url}"
    browse(url)
  end

  desc "Run a remote Jenkins build"
  task :remote_build => [:apikey] do
    notice("Running remote Jenkins build")
    job_url = Jenkins.job_url(:task=>'BUILD')
    api_key = Jenkins.read_api_key
    build_url = "#{job_url}/build?token=#{api_key}"
    sh "curl -k --user $USER -X POST --data '{}' '#{build_url}'"
    notice("Job queued for building")
  end

  desc "Run a local build"
  task :build => ["setup:install", :test, "setup:pynest", :component_rpmbuild, "doc:publish"]

  desc "Run a local build, without publishing docs"
  task :build_no_docs => ["setup:install", :test, "setup:pynest", :component_rpmbuild]

  desc "If this is a component, build an RPM, otherwise do nothing"
  task :component_rpmbuild do
    if Project[:IS_COMPONENT]
      Rake::Task["rpm:build"].invoke
    end
  end

  desc "Initialize the Jenkins config for a build job"
  task :createxml_build do
    Jenkins.create_config_xml(:task => 'BUILD')
  end

  desc "Initialize the Jenkins config for a CI integration test job"
  task :createxml_ci_integrationtest do
    Jenkins.create_config_xml(:task => 'CI-INTEGRATIONTEST')
  end

  desc "Initialize the Jenkins config for a QA deploy job"
  task :createxml_qa_deploy do
    Jenkins.create_config_xml(:task => 'QA-DEPLOY')
  end

  desc "Perform an autorelease using parameters set in environment variables"
  task :deploy do
    notice("Autoreleasing")
    require_env('ENVIRONMENT', 'Set ENVIRONMENT to the environment to deploy into (e.g. futureqa)')
    require_env('TARGET', 'Set TARGET to the hostclass to deploy into')
    # RELEASE_VERSION may also be set, but is not required
    # REFSPEC may also be set, but is not required

    io = WGR.autorelease(ENV['TARGET'], ENV['ENVIRONMENT'],
                    ENV['RELEASE_VERSION'], ENV['REFSPEC'])
    output = io.read
    puts output
    io.close

    if $?.exitstatus != 0
      error "Autorelease failed with exit status #{$?.exitstatus}" 
    else
      good "Autorelease complete."
    end

  end

  desc "Deploy, then run integration tests"
  task :deploy_and_test => [:deploy, "test:integration"]

  desc "Perform the CI integration tests, then promote the CI build to QA"
  task :ci_integrationtest => [:deploy_and_test, :promote_ci_to_qa]

  desc "Promote the currently installed CI build to the QA repository"
  task :promote_ci_to_qa do
    require_env('ENVIRONMENT', 'Set ENVIRONMENT to the CI environment to migrate from')
    require_env('CI_REPO', 'Set CI_REPO to the repository to promote the RPM from')
    require_env('QA_REPO', 'Set QA_REPO to the repository to promote the RPM to')

    # Determine which version of the RPM is installed
    rpm, version, build = RPM.rpm_version(ENV['ENVIRONMENT'])
    error("Couldn't determine an installed RPM") unless rpm
    notice "Promoting RPM #{rpm}-#{version}-#{build} from CI to QA"

    # Copy from the CI repo to the QA repo
    ci_file_glob = "#{rpm}-#{version}-#{build}*.rpm"
    ci_glob = "#{ENV['CI_REPO']}/#{ci_file_glob}"
    ci_files = Dir.glob(ci_glob)
    if ci_files.empty?
      error("Couldn't find the CI RPM in the repo; looked for #{ci_glob}")
    end
    FileUtils.cp ci_files[0], ENV['QA_REPO']

    good "Promoted RPM #{rpm}-#{version}-#{build} from CI to QA"
    good "Post-deployment component integration tests complete"
  end

  desc "Obtain Jenkins API key"
  task :apikey do
    begin
      api_key = Jenkins.read_api_key
    rescue IOError => e
      notice(e.to_s)
      api_key = Jenkins.ask_api_key
    rescue Exception => e
      error(e.to_s)
    end
    notice("Have a Jenkins API key")
  end
end
