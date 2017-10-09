# -----------------------------------------------------
# Git tasks.
# -----------------------------------------------------
require 'pathname'

module Git
  def self.get_origin
    remote_fulltext = `git remote show origin`
    if $?.to_i != 0
      raise lowlight("Can't determine the git origin")
    end
    match = remote_fulltext.match(/Fetch URL: (.+)/)
    if ! match
      raise lowlight("Can't determine the git origin")
    end

    origin = match[1]
    origin
  end

  def self.get_current_branch
    current_ref = `git symbolic-ref HEAD`.strip
    raise lowlight('There is no current git branch.') if current_ref.empty?
    current_branch = current_ref.sub('refs/heads/', '')
    current_branch
  end

  def self.get_current_hash
    current_hash = `git rev-parse HEAD`.strip

    raise lowlight("Can't determine the current git hash") if current_hash.empty?
    return current_hash
  end

  #
  # Returns the git root directory
  #
  def self.get_root
    root_dir = `git rev-parse --show-toplevel`.strip
    if $?.to_i != 0
      raise lowlight("Can't determine the root git directory")
    end
    return root_dir
  end

  #
  # Returns true if the cwd is within a git repo
  #
  def self.is_git_repo
    git_dir = `git rev-parse --git-dir 2> /dev/null`.strip
    return ($?.to_i == 0)
  end

  #
  # Returns the path from the root of the git repo to the current
  # directory.
  #
  def self.get_path_from_root
    root_dir = get_root
    cwd = Dir.pwd
    relative_path = Pathname.new(cwd).relative_path_from(Pathname.new(root_dir)).to_s
    return relative_path
  end
end

module Hub
  def self.get_github_repo_url
    base_url = `hub --noop browse | awk '{print $2}'`.strip
    return base_url
  end

  def self.get_github_project_url
    base_url = get_github_repo_url
    path = Git.get_path_from_root
    url = (path == '.') ? base_url : "#{base_url}/tree/master/#{path}"
    return url
  end
end

namespace :git do

  desc 'Verify that hub is installed and configured'
  task :verify_hub do
    hub = `which hub`.strip
    hub_instructions = "Instructions to configure hub: http://goo.gl/HNycga"
    if ! hub
      fail(lowlight('hub is not available.') + hub_instructions)
    end

    hub_hosts = `hub config --global --get-all hub.host`.strip
    if ! hub_hosts.match(Project[:GITHUB_HOST])
      fail(lowlight("hub.host not configured for #{Project[:GITHUB_HOST]}") + hub_instructions)
    end

    if ! ENV.include?('GITHUB_HOST') or ENV['GITHUB_HOST'] != Project[:GITHUB_HOST]
      fail(lowlight("GITHUB_HOST not configured for #{Project[:GITHUB_HOST]}") + hub_instructions)
    end
  end

  desc 'Create a new repository'
  task :create => [:verify_hub] do
    notice("Creating a new git repository")
    repo = "#{Project[:ORGANIZATION]}/#{Project[:PROJECT]}"
    is_existing_repo = Git.is_git_repo
    if is_existing_repo then
      fail(lowlight('This is already a git repository.'))
    end
    sh "git init"
    sh "git add ."
    sh "git commit -m 'Initial commit of #{Project[:PROJECT]}'"
    is_repo_created = system("hub", "create", repo, "-d", Project[:DESCRIPTION], "-h", Project[:URL])
    if is_repo_created != true then
      fail(lowlight("Could not create #{repo} on Github:WGEN"))
    end
    current_branch = Git.get_current_branch()
    sh "git push -u origin #{current_branch}"
    sh "hub browse"
    good("New repository created: #{repo}")
    github_url = Hub.get_github_repo_url
    puts "Repository URL: #{github_url}"
  end

  desc 'Commit the changes to the git repository.'
  task :commit => [:lint] do
    sh "git commit --dry-run -a -u -m '.'"
    commit_confirmation = ask('Should I actually commit [Y/n]: ')
    if commit_confirmation != 'n' then
      commit_message = ask('Please insert your commit message: ')
      sh "git commit -a -u -m '#{commit_message}'"
    end
  end

  desc 'Push the changes to the remote git repository.'
  task :push => [:test] do
    sh "git push"
  end

  desc 'Push the changes to the remote git repository (to current branch).'
  task :push_to_branch => [:test] do
    current_branch = Git.get_current_branch()
    sh "git push origin #{current_branch}"
  end

  desc 'Pull the changes from the remote git repository using --rebase.'
  task :pull do
    sh "git pull --rebase"
  end
end
