# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Copyright (c) 2017-2019, Battelle Memorial Institute; Lawrence Livermore
# National Security, LLC; Alliance for Sustainable Energy, LLC.
# See the top-level NOTICE for additional details.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

cmake_minimum_required(VERSION 3.4)
cmake_policy(VERSION 3.4)

project (HELICS-EXAMPLES VERSION 2.3.0)

# -----------------------------------------------------------------------------
# include some common macros
# -----------------------------------------------------------------------------
set_property(GLOBAL PROPERTY USE_FOLDERS ON)
include(GNUInstallDirs)

# -------------------------------------------------------------
# setting the RPATH
# -------------------------------------------------------------
# use, i.e. don't skip the full RPATH for the build tree
set(CMAKE_SKIP_BUILD_RPATH  FALSE)

# when building, don't use the install RPATH already (but later on when installing)
set(CMAKE_BUILD_WITH_INSTALL_RPATH FALSE)

set(CMAKE_MACOSX_RPATH ON)

# add the automatically determined parts of the RPATH which point to directories outside
# the build tree to the install RPATH
set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)

# the RPATH to be used when installing, but only if it's not a system directory
list(
  FIND
    CMAKE_PLATFORM_IMPLICIT_LINK_DIRECTORIES
    "${CMAKE_INSTALL_PREFIX}/${CMAKE_INSTALL_BINDIR}" isSystemDir
)
if("${isSystemDir}" STREQUAL "-1")
  list(
    APPEND
      CMAKE_INSTALL_RPATH CMAKE_INSTALL_RPATH
      "${CMAKE_INSTALL_PREFIX}/${CMAKE_INSTALL_BINDIR}"
  )
endif()

list(
  FIND
    CMAKE_PLATFORM_IMPLICIT_LINK_DIRECTORIES
    "${CMAKE_INSTALL_PREFIX}/${CMAKE_INSTALL_LIBDIR}" isSystemDir
)
if("${isSystemDir}" STREQUAL "-1")
    list(APPEND CMAKE_INSTALL_RPATH "${CMAKE_INSTALL_PREFIX}/${CMAKE_INSTALL_LIBDIR}")
endif()


# add the local directory to the rpath
list(APPEND CMAKE_INSTALL_RPATH "./")


# -----------------------------------------------------------------------------
# CMAKE Subdirectories
# -----------------------------------------------------------------------------

OPTION(ENABLE_C_EXAMPLES "Enable the C based examples to be built" ON)
OPTION(ENABLE_CPP_EXAMPLES "Enable the C++ based examples to be built" ON)
OPTION(ENABLE_CPP98_EXAMPLES "Enable the C++98 based examples to be built" ON)

if (ENABLE_C_EXAMPLES)
    add_subdirectory(c)
endif()

if (ENABLE_CPP_EXAMPLES)
  add_subdirectory(cpp)
endif()

if (ENABLE_CPP98_EXAMPLES)
  add_subdirectory(cpp98)
endif()
