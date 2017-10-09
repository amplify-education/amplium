module Pylint
  module Status
    OK = 0
    FATAL = 1
    ERROR = 2
    WARNING = 4
    REFACTOR = 8
    CONVENTION = 16
    USAGE = 32
  end

  def self.status_is_success(status)
    is_status = lambda { |other_status|
      (status & other_status) != 0
    }

    is_fatal = is_status.call(Status::OK)
    is_error = is_status.call(Status::ERROR)
    is_warning = is_status.call(Status::WARNING)
    is_refactor = is_status.call(Status::REFACTOR)
    is_convention = is_status.call(Status::CONVENTION)

    puts "Status: #{status}"
    puts "is_fatal: #{is_fatal}"
    puts "is_error: #{is_error}"
    puts "is_warning: #{is_warning}"
    puts "is_refactor: #{is_refactor}"
    puts "is_convention: #{is_convention}"

    return !(is_fatal or is_error or is_warning or is_refactor or is_convention)
  end
end

module Config
  def self.merge_config(name)
    base_config_file = "#{ProjectPaths::LINT_DIR}/#{name}"
    user_config_file = "#{base_config_file}_user"
    new_config_file = "#{base_config_file}_merged"

    sh "python #{ProjectPaths::LINT_DIR}/merge_config.py #{base_config_file} #{user_config_file} #{new_config_file}"
    return new_config_file
  end
end

namespace "lint" do
  desc "Install lint dependencies"
  task :install => ["test:install"]

  desc "Run pep8 on the package and test files"
  task :pep8 => [:install] do
    notice("Linting with pep8")
    pep8_paths = [ProjectPaths::PACKAGE_DIR]
    if Project[:IS_TEST_DIR_PEP8]
      pep8_paths.push(ProjectPaths::TEST_DIR)
    end
    pep8_path_arg = pep8_paths.join(" ")
    rc_file = Config.merge_config("pep8rc")
    sh "pep8 --config=#{rc_file} #{pep8_path_arg}" do |ok, status|
      rm rc_file
      ok or fail(lowlight("pep8 failed"))
    end
    good("pep8 passed")
  end

  desc "Run pylint on the package and test files"
  task :pylint => [:install] do
    notice("Linting with pylint")
    format = $stdout.isatty ? "colorized" : "text"
    pylint_paths = [ProjectPaths::PACKAGE_DIR]
    if Project[:IS_TEST_DIR_PYLINT]
      pylint_paths.push(ProjectPaths::TEST_DIR)
    end
    pylint_path_arg = pylint_paths.join(" ")
    rc_file = Config.merge_config("pylintrc")
    sh "pylint --rcfile=#{rc_file} --output-format=#{format} #{pylint_path_arg}" do |ok, status|
      rm rc_file
      status_is_success = Pylint.status_is_success(status.exitstatus)
      status_is_success or fail(lowlight("pylint failed"))
    end
    good("pylint passed")
  end
end

desc "Run all source code analysis tools"
task :lint => ["lint:pep8", "lint:pylint"]
