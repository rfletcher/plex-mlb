require 'rake'
require 'rake/clean'
require 'rake/packagetask'
require 'xml'

PLEXMLB_BUNDLE_ID        = 'com.plexapp.plugins.mlb'
PLEXMLB_BUNDLE_NAME      = 'Major League Baseball.bundle'
PLEXMLB_SITE_CONFIG_NAME = PLEXMLB_BUNDLE_ID.split('.').last + '.xml'

PLEXMLB_ROOT         = File.expand_path( File.dirname( __FILE__ ) )
PLEXMLB_SRC_DIR      = File.join( PLEXMLB_ROOT, 'src' )
PLEXMLB_DIST_DIR     = File.join( PLEXMLB_ROOT, 'dist' )

PLEX_SUPPORT_DIR     = File.expand_path( '~/Library/Application Support/Plex Media Server' )
PLEX_PLUGIN_DIR      = File.join( PLEX_SUPPORT_DIR, 'Plug-ins' )
PLEX_SITE_CONFIG_DIR = File.join( PLEX_SUPPORT_DIR, 'Site Configurations' )

task :default => [ 'dist:release', :clean_package_source ]

CLOBBER.include( PLEXMLB_DIST_DIR )

desc 'Build the distribution.'
namespace :dist do
  desc 'Build a dev distribution.'
  task :dev => :release do
    # enable dev related properties in Info.plist
    plist_filename = File.join( PLEXMLB_DIST_DIR, PLEXMLB_BUNDLE_NAME, 'Contents/Info.plist' )
    doc = XML::Parser.file( plist_filename ).parse

    [ 'PlexPluginDebug', 'PlexPluginDevMode' ].each do |element|
      val_el = doc.find_first( "//key[text()='#{element}']/following-sibling::string" )
      val_el.content = "1" if val_el
    end

    doc.save( plist_filename )
  end

  desc 'Build a release distribution.'
  task :release do
    rm_if_exists File.join( PLEXMLB_DIST_DIR )
    bundle_dest = File.join( PLEXMLB_DIST_DIR, PLEXMLB_BUNDLE_NAME )
    mkdir_p( bundle_dest )
    cp_r File.join( PLEXMLB_SRC_DIR, 'bundle' ), File.join( bundle_dest, 'Contents' )
    cp_r File.join( PLEXMLB_SRC_DIR, 'site configuration.xml' ), File.join( PLEXMLB_DIST_DIR, PLEXMLB_SITE_CONFIG_NAME )    
  end
end
task :dist => 'dist:dev'

desc 'Clean up source dir left behind by `rake package`'
task :clean_package_source do
  rm_if_exists File.join( PLEXMLB_PKG_DIR, "plex-mlb")
end

desc 'Install the bundle'
task :install => 'dist:dev' do
  rm_if_exists File.join( PLEX_PLUGIN_DIR, PLEXMLB_BUNDLE_NAME )
  rm_if_exists File.join( PLEX_SITE_CONFIG_DIR, PLEXMLB_SITE_CONFIG_NAME )

  cp_r File.join( PLEXMLB_DIST_DIR, PLEXMLB_BUNDLE_NAME ), File.join( PLEX_PLUGIN_DIR, PLEXMLB_BUNDLE_NAME )
  cp_r File.join( PLEXMLB_DIST_DIR, PLEXMLB_SITE_CONFIG_NAME ), File.join( PLEX_SITE_CONFIG_DIR, PLEXMLB_SITE_CONFIG_NAME )
end

def rm_if_exists file
  rm_rf file if File.exists? file
end
