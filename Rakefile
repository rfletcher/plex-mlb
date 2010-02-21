require 'rubygems'
require 'rake'
require 'rake/clean'
require 'rake/packagetask'
require 'appscript'
require 'tempfile'
require 'yaml'

# base paths
PLUGIN_ROOT         = File.expand_path( File.dirname( __FILE__ ) )
PLUGIN_BUNDLE_DIR   = File.join( PLUGIN_ROOT, 'bundle' )
PLUGIN_BUILD_DIR    = File.join( PLUGIN_ROOT, 'build' )

# paths used by the :install task
DIR_APP_SUPPORT     = File.expand_path( '~/Library/Application Support' )
PLEX_SUPPORT_DIR    = File.join( DIR_APP_SUPPORT, 'Plex' )
PMS_SUPPORT_DIR     = File.join( DIR_APP_SUPPORT, 'Plex Media Server' )
PMS_PLUGIN_DIR      = File.join( PMS_SUPPORT_DIR, 'Plug-ins' )
PMS_PLUGIN_DATA_DIR = File.join( PMS_SUPPORT_DIR, 'Plug-in Support' )

PMS_BIN = File.join( PLEX_SUPPORT_DIR, 'Plex Media Server.app', 'Contents', 'MacOS', 'Plex Media Server' )

class File
  def self.binary?( name )
    fstat = stat( name )
    if !fstat.file?
      false
    else
      open( name ) do |file|
        blk = file.read( fstat.blksize )
        blk.size == 0 || blk.count( "^ -~", "^\r\n" ) / blk.size > 0.3 || blk.count( "\x00" ) > 0
      end
    end
  end

  def self.rm_if_exists( name )
    rm_rf name if self.exists? name
  end
end

def bundle_name config
  ( config['PLUGIN_BUNDLE_NAME'] ? config['PLUGIN_BUNDLE_NAME'] : config['PLUGIN_NAME'] ) + '.bundle'
end

def erb config, file
  temp = Tempfile.new( "erb" )
  File.open( file ).each_line do |line|
    temp << line.gsub( /<%=(.*?)%>/ ) do
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
  YAML.load_file( File.join( PLUGIN_ROOT, 'config.yml' ) )[env.to_s]
end

config = load_config

PLUGIN_PACKAGE_NAME = "#{config['PLUGIN_NAME']}-#{config['PLUGIN_VERSION']}".gsub " ", "_"

# files to blow away with a `rake clobber`
CLOBBER.include( PLUGIN_BUILD_DIR, "#{PLUGIN_PACKAGE_NAME}.tar.gz" )

task :default => :build

namespace :build do
  desc 'Build a dev distribution.'
  task :development do
    config = load_config :development
    Rake::Task["build:release"].execute
    touch File.join( PLUGIN_BUILD_DIR, bundle_name( config ), "development" )
  end
  task :dev => :development

  desc 'Build a release distribution.'
  task :release do
    File.rm_if_exists File.join( PLUGIN_BUILD_DIR )
    bundle_dest = File.join( PLUGIN_BUILD_DIR, bundle_name( config ) )
    mkdir_p bundle_dest
    cp_r File.join( PLUGIN_BUNDLE_DIR ), File.join( bundle_dest, 'Contents' )
    cp_r File.join( PLUGIN_ROOT, 'config.yml' ), File.join( bundle_dest, 'Contents', 'Code' )

    readme = Dir["README*"].first
    cp_r readme, File.join( PLUGIN_BUILD_DIR, "README.txt" ) if readme

    # process files with some poor-man's erb
    FileList[ File.join( PLUGIN_BUILD_DIR, '**', '*' ) ].find_all { |file|
      # skip the Libraries dir
      !file.match File.join( bundle_dest, 'Contents', 'Libraries' )
    }.each { |file|
      erb config, file unless ( File.directory?( file ) || File.binary?( file ) )
    }
  end
end
desc 'Alias for build:release'
task :build => 'build:release'

desc 'Create an installable plex app, suitable for distribution'
task :package => 'build:release' do
  Appscript.app("AppMaker").activate

  se = Appscript.app("System Events")
  am = se.processes["AppMaker"]
  am_window = am.windows["AppMaker"]

  am_window.actions["AXRaise"].perform

  [ File.join( PLUGIN_BUILD_DIR, bundle_name( config ) ),
    config['PLUGIN_NAME'],
    config['PLUGIN_AUTHOR'],
    config['PLUGIN_VERSION'],
    config['PLUGIN_DESCRIPTION']
  ].each_with_index do |value, i|
    i += 1
    am_window.text_fields[i].value.set( value )
    am_window.text_fields[i].focused.set( true )
    if i == 1
      am_window.text_fields[i].actions["AXConfirm"].perform
    else
      am_window.text_fields[i].key_code( 124 )
      am_window.text_fields[i].keystroke( " \b" )
    end
  end

  am_window.UI_elements["Create Package"].click
  am.keystroke( "g", :using => [ :command_down, :shift_down ] )
  am.keystroke( PLUGIN_BUILD_DIR + "\r" )
  am.keystroke( config['PLUGIN_NAME'] + "\r" )

  # wait for save
  am_window.text_fields[1].focused.set( true )

  Appscript.app("AppMaker").quit
end

namespace :pms do
  task :restart => [ :stop, :start ]

  desc 'Start Plex Media Server'
  task :start do
    exec '"' + PMS_BIN + '"'
  end

  task :stop do
    system "killall",  "Plex Media Server"
  end
end
task :pms => 'pms:restart'

namespace :install do
  desc 'Install a clean copy (do an uninstall:hard first)'
  task :clean => [ 'uninstall:hard', :install ]

  desc 'Install a development version of the plugin'
  task :development => [ 'build:development', :install ]
  task :dev => :development

  desc 'Install a release version of the plugin'
  task :release => [ 'build:release', :install ]

  task :install => :uninstall do
    mkdir_p File.join( PMS_PLUGIN_DIR, bundle_name( config ) )
    cp_r File.join( PLUGIN_BUILD_DIR, bundle_name( config ) ), PMS_PLUGIN_DIR
  end
end
desc 'Alias for install:release'
task :install => 'install:release'

namespace :uninstall do
  desc 'Remove the installed bundle, but leave data behind.'
  task :soft do
    File.rm_if_exists File.join( PMS_PLUGIN_DIR, bundle_name( config ) )
  end

  desc 'Remove the installed bundle and data.'
  task :hard => :soft do
    files = FileList[
      File.join( PMS_PLUGIN_DATA_DIR, "*", "#{config['PLUGIN_ID']}.*" ),
      File.join( PMS_PLUGIN_DATA_DIR, "*", "#{config['PLUGIN_ID']}" ),
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
    system "tail -f " << logs.collect { |log| "\"#{log}\"" }.join( ' ' )
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
