require 'rake'
require 'rake/clean'
require 'rake/packagetask'
require "tempfile"
require 'yaml'

# base paths
PLUGIN_ROOT         = File.expand_path( File.dirname( __FILE__ ) )
PLUGIN_BUNDLE_DIR   = File.join( PLUGIN_ROOT, 'bundle' )
PLUGIN_BUILD_DIR    = File.join( PLUGIN_ROOT, 'build' )

# paths used by the :install task
PLEX_SUPPORT_DIR     = File.expand_path( '~/Library/Application Support/Plex Media Server' )
PLEX_PLUGIN_DIR      = File.join( PLEX_SUPPORT_DIR, 'Plug-ins' )
PLEX_PLUGIN_DATA_DIR = File.join( PLEX_SUPPORT_DIR, 'Plug-in Support' )

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
    FileList[ File.join( PLUGIN_ROOT, 'README*' ) ].each do |file|
      cp_r file, PLUGIN_BUILD_DIR
    end

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

desc 'Create a tarball, suitable for distribution'
task :package => 'build:release' do
  Dir.chdir PLUGIN_BUILD_DIR do
    contents = Dir.glob( "*" )
    mkdir_p PLUGIN_PACKAGE_NAME
    mv contents, PLUGIN_PACKAGE_NAME
    system "tar czf #{PLUGIN_PACKAGE_NAME}.tar.gz #{PLUGIN_PACKAGE_NAME}"
    mv "#{PLUGIN_PACKAGE_NAME}.tar.gz", PLUGIN_ROOT
  end
end

namespace :install do
  desc 'Install a clean copy (do an uninstall:hard first)'
  task :clean => [ 'uninstall:hard', :install ]

  desc 'Install a development version of the plugin'
  task :development => [ 'build:development', :install ]
  task :dev => :development

  desc 'Install a release version of the plugin'
  task :release => [ 'build:release', :install ]

  task :install => :uninstall do
    mkdir_p File.join( PLEX_PLUGIN_DIR, bundle_name( config ) )
    cp_r File.join( PLUGIN_BUILD_DIR, bundle_name( config ) ), PLEX_PLUGIN_DIR
  end
end
desc 'Alias for install:release'
task :install => 'install:release'

namespace :uninstall do
  desc 'Remove the installed bundle, but leave data behind.'
  task :soft do
    File.rm_if_exists File.join( PLEX_PLUGIN_DIR, bundle_name( config ) )
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
