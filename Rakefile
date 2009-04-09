# rake -l

require 'rake'
require 'rake/clean'
require 'rake/packagetask'

PLEXMLB_ROOT          = File.expand_path(File.dirname(__FILE__))
PLEXMLB_SRC_DIR       = File.join(PLEXMLB_ROOT, 'src')
PLEXMLB_DIST_DIR      = File.join(PLEXMLB_ROOT, 'dist')
PLEXMLB_INSTALL_BASE  = '~/Library/Application Support/Plex Media Server'
# PLEXMLB_TMP_DIR       = File.join(PLEXMLB_TEST_UNIT_DIR, 'tmp')

task :default => [:dist, :package, :clean_package_source]

CLOBBER.include( PLEXMLB_DIST_DIR, PLEXMLB_TMP_DIR )

Rake::PackageTask.new('tagbox', PLEXMLB_VERSION) do |package|
  package.need_tar_gz = true
  package.package_dir = PLEXMLB_PKG_DIR
  package.package_files.include(
    'README*',
    'assets/**',
    'demo/**',
    'demo/flags/**',
    'dist/tagbox.js'
  )
end

desc 'Push the latest demo to gh-pages'
task :install => :dist do
  require "grancher"

  grancher = Grancher.new do |g|
    g.branch = 'gh-pages'
    g.push_to = 'origin'
    g.message = "Updated demo, v#{PLEXMLB_VERSION}"

    # Copy the files needed for the demo
    g.directory 'assets', 'assets'
    g.directory 'demo', 'demo'
    g.directory 'dist', 'dist'
  end

  grancher.commit
  grancher.push
end