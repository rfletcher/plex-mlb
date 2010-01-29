require 'rake'
require 'rake/clean'
require 'rake/packagetask'
require "tempfile"
require 'yaml'

# base paths
PLEXMLB_ROOT         = File.expand_path( File.dirname( __FILE__ ) )
PLEXMLB_SRC_DIR      = File.join( PLEXMLB_ROOT, 'src' )
PLEXMLB_LIB_DIR      = File.join( PLEXMLB_ROOT, 'lib' )
PLEXMLB_DIST_DIR     = File.join( PLEXMLB_ROOT, 'dist' )

# paths used by the :install task
PLEX_SUPPORT_DIR     = File.expand_path( '~/Library/Application Support/Plex Media Server' )
PLEX_PLUGIN_DIR      = File.join( PLEX_SUPPORT_DIR, 'Plug-ins' )
PLEX_PLUGIN_DATA_DIR = File.join( PLEX_SUPPORT_DIR, 'Plug-in Support' )

class File
  def self.binary?(name)
    fstat = stat(name)
    if !fstat.file?
      false
    else
      open(name) do |file|
        blk = file.read(fstat.blksize)
        blk.size == 0 || blk.count("^ -~", "^\r\n") / blk.size > 0.3 || blk.count("\x00") > 0
      end
    end
  end
end

def bundle_name config
  ( config['PLUGIN_BUNDLE_NAME'] ? config['PLUGIN_BUNDLE_NAME'] : config['PLUGIN_NAME'] ) + '.bundle'
end

def erb config, file
  temp = Tempfile.new( "erb" )
  File.open( file ).each_line do |line|
    temp << line.gsub(/<%=(.*?)%>/) do
      prop = $1.strip
      if value = config[prop]
        value
      else
        raise "couldn't find property `#{prop}' (in #{file})"
      end
    end
  end
  temp.close

  mv( temp.path, file, :verbose => false )
end

def load_config env=:release
  YAML.load_file( File.join( PLEXMLB_SRC_DIR, 'config.yml' ) )[env.to_s]
end

def rm_if_exists file
  rm_rf file if File.exists? file
end

def site_config_name config
  config['PLUGIN_ID'].split('.').last + '.xml'
end

config = load_config

PLEXMLB_PACKAGE_NAME = "#{config['PLUGIN_NAME']}-#{config['PLUGIN_VERSION']}".gsub " ", "_"

# files to blow away with a `rake clobber`
CLOBBER.include( PLEXMLB_DIST_DIR, "#{PLEXMLB_PACKAGE_NAME}.tar.gz" )

task :default => :dist

namespace :dist do
  desc 'Build a dev distribution.'
  task :development do
    config = load_config :development
    Rake::Task["dist:release"].execute
    touch File.join( PLEXMLB_DIST_DIR, bundle_name( config ), "development" )
  end

  desc 'Build a release distribution.'
  task :release do
    rm_if_exists File.join( PLEXMLB_DIST_DIR )
    bundle_dest = File.join( PLEXMLB_DIST_DIR, bundle_name( config ) )
    mkdir_p( bundle_dest )
    cp_r File.join( PLEXMLB_SRC_DIR, 'bundle' ), File.join( bundle_dest, 'Contents' )
    cp_r File.join( PLEXMLB_SRC_DIR, 'config.yml' ), File.join( bundle_dest, 'Contents', 'Code' )
    cp_r File.join( PLEXMLB_ROOT, 'README.rst' ), PLEXMLB_DIST_DIR

    # process files with erb
    FileList[ File.join( PLEXMLB_DIST_DIR, '**', '*' ) ].exclude().each do |file|
      erb config, file unless ( File.directory?( file ) || File.binary?( file ) )
    end

    cp_r PLEXMLB_LIB_DIR, File.join( bundle_dest, 'Contents', 'Libraries' )
  end
end
desc 'Alias for dist:release'
task :dist => 'dist:release'

desc 'Create a tarball, suitable for distribution'
task :package => 'dist:release' do
  Dir.chdir PLEXMLB_DIST_DIR do
    contents = Dir.glob( "*" )
    mkdir_p PLEXMLB_PACKAGE_NAME
    mv contents, PLEXMLB_PACKAGE_NAME
    system "tar czf #{PLEXMLB_PACKAGE_NAME}.tar.gz #{PLEXMLB_PACKAGE_NAME}"
    mv "#{PLEXMLB_PACKAGE_NAME}.tar.gz", PLEXMLB_ROOT
  end
end

namespace :install do
  desc 'Install a development version of the plugin'
  task :development => [ 'dist:development', :install ]

  desc 'Install a release version of the plugin'
  task :release => [ 'dist:release', :install ]

  task :install => :uninstall do
    cp_r File.join( PLEXMLB_DIST_DIR, bundle_name( config ) ), File.join( PLEX_PLUGIN_DIR, bundle_name( config ) )
  end
end
desc 'Alias for install:development'
task :install => 'install:development'

namespace :uninstall do
  desc 'Remove the installed bundle, but leave data behind.'
  task :soft do
    rm_if_exists File.join( PLEX_PLUGIN_DIR, bundle_name( config ) )
  end

  desc 'Remove the installed bundle and data.'
  task :hard => :soft do
    files = FileList[
      File.join( PLEX_PLUGIN_DATA_DIR, "*", "#{config['PLUGIN_ID']}.*" ),
      File.join( PLEX_PLUGIN_DATA_DIR, "*", "#{config['PLUGIN_ID']}" ),
    ]
    rm_rf files unless files.empty?
  end
end
desc 'Alias for uninstall:soft'
task :uninstall => 'uninstall:soft'

namespace :tail do
  logs = {
    :plex => [ 'Plex', File.expand_path( "~/Library/Logs/Plex.log" ) ],
    :plugin => [ 'the plugin', File.expand_path( "~/Library/Logs/PMS Plugin Logs/#{config['PLUGIN_ID']}.log" ) ]
  }

  def tail logs
    system "tail -f " << logs.collect { |log| "\"#{log}\"" }.join(' ')
  end

  logs.each do |k,v|
    desc "Tail #{v[0]}'s log file"
    task( k ) { tail [v[1]] }
  end

  desc 'Tail log files'
  task :all do
    tail logs.collect { |k,v| v[1] }
  end
end
desc 'Alias for tail:all'
task :tail => 'tail:all'
