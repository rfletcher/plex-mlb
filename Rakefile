require 'rake'
require 'rake/clean'
require 'rake/packagetask'

PLEXMLB_BUNDLE_ID        = 'com.plexapp.plugins.mlb'
PLEXMLB_BUNDLE_NAME      = 'Major League Baseball.bundle'
PLEXMLB_SITE_CONFIG_NAME = PLEXMLB_BUNDLE_ID.split('.').last + '.xml'

PLEXMLB_ROOT         = File.expand_path( File.dirname( __FILE__ ) )
PLEXMLB_SRC_DIR      = File.join( PLEXMLB_ROOT, 'src' )
PLEXMLB_DIST_DIR     = File.join( PLEXMLB_ROOT, 'dist' )
PLEXMLB_PKG_DIR      = File.join( PLEXMLB_ROOT, 'pkg' )

PLEX_SUPPORT_DIR     = File.expand_path( '~/Library/Application Support/Plex Media Server' )
PLEX_PLUGIN_DIR      = File.join( PLEX_SUPPORT_DIR, 'Plug-ins' )
PLEX_SITE_CONFIG_DIR = File.join( PLEX_SUPPORT_DIR, 'Site Configurations' )

task :default => [ :dist, :package, :clean_package_source ]

CLOBBER.include( PLEXMLB_DIST_DIR )

desc 'Builds the distribution.'
task :dist do
  mkdir( PLEXMLB_DIST_DIR ) unless File.directory? PLEXMLB_DIST_DIR
  cp_r File.join( PLEXMLB_SRC_DIR, 'bundle' ), File.join( PLEXMLB_DIST_DIR, PLEXMLB_BUNDLE_NAME )
  cp_r File.join( PLEXMLB_SRC_DIR, 'site configuration.xml' ), File.join( PLEXMLB_DIST_DIR, PLEXMLB_SITE_CONFIG_NAME )
end

Rake::PackageTask.new( 'plex-mlb', :noversion ) do |package|
  package.need_tar_gz = true
  package.package_dir = PLEXMLB_PKG_DIR
  package.package_files.include(
    'README*',
    'dist/**'
  )
end

desc 'Clean up source dir left behind by `rake package`'
task :clean_package_source do
  rm_if_exists File.join( PLEXMLB_PKG_DIR, "plex-mlb")
end

desc 'Install the bundle'
task :install => :dist do
  rm_if_exists File.join( PLEX_PLUGIN_DIR, PLEXMLB_BUNDLE_NAME )
  rm_if_exists File.join( PLEX_SITE_CONFIG_DIR, PLEXMLB_SITE_CONFIG_NAME )

  cp_r File.join( PLEXMLB_DIST_DIR, PLEXMLB_BUNDLE_NAME ), File.join( PLEX_PLUGIN_DIR, PLEXMLB_BUNDLE_NAME )
  cp_r File.join( PLEXMLB_DIST_DIR, PLEXMLB_SITE_CONFIG_NAME ), File.join( PLEX_SITE_CONFIG_DIR, PLEXMLB_SITE_CONFIG_NAME )
end

def rm_if_exists file
  rm_rf file if File.exists? file
end
