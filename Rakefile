# rake -l

require 'rake'
require 'rake/clean'
require 'rake/packagetask'

PLEXMLB_BUNDLE_NAME    = 'Major League Baseball'
PLEXMLB_BUNDLE_ID      = 'com.plexapp.plugins.mlb'

PLEXMLB_ROOT         = File.expand_path( File.dirname( __FILE__ ) )
PLEXMLB_SRC_DIR      = File.join( PLEXMLB_ROOT, 'src' )
PLEXMLB_DIST_DIR     = File.join( PLEXMLB_ROOT, 'dist' )
PLEXMLB_PKG_DIR      = File.join( PLEXMLB_ROOT, 'pkg' )

task :default => [ :dist, :package, :clean_package_source ]

CLOBBER.include( PLEXMLB_DIST_DIR, PLEXMLB_PKG_DIR )

desc 'Builds the distribution.'
task :dist do
  mkdir( PLEXMLB_DIST_DIR ) unless File.directory? PLEXMLB_DIST_DIR
  cp_r( PLEXMLB_SRC_DIR + '/bundle', PLEXMLB_DIST_DIR + '/' + PLEXMLB_BUNDLE_NAME + '.bundle' )
  cp_r( PLEXMLB_SRC_DIR + '/site configuration.xml', PLEXMLB_DIST_DIR + '/' + PLEXMLB_BUNDLE_ID.split('.').last + '.xml' )
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
  rm_rf File.join( PLEXMLB_PKG_DIR, "plex-mlb"), :verbose => false
end
