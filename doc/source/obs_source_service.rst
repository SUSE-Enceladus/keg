.. _keg_obs_source_service:

Keg OBS Source Service
======================

The `OBS Source Service` for `keg` provides a mechanism to produce `kiwi` image
descriptions for use with the `Open Build Service
<https://openbuildservice.org/help/manuals/obs-user-guide/>`_ in an automated
fashion. The `OBS Source Service`, named `compose_kiwi_description`, checks
out any given `keg-recipes` repositories, runs `keg` to produce the specified
image description, and optionally produces change log files and stores the
HEAD commit hashed of the `keg-recipes` repositories to be used for the next
source service run.

To set up an `OBS` package as a `keg` source service package, simply create a
file named :file:`_service` in your package directory. The contents of the
file should look like the following:

.. code:: xml

   <services>
       <service name="compose_kiwi_description">
           <param name="git-recipes">https://github.com/SUSE-Enceladus/keg-recipes.git</param>
           <param name="git-branch">released</param>
           <param name="image-source">cross-cloud/sles/byos/15-sp3</param>
       </service>
   </services>

In this example, the `released` branch of the public `keg-recipes` repository
for SUSE Linux Enterprise images hosted on github is used as source and the
selected image source is `cross-cloud/sles/byos/15-sp3`. Running the source
service will produce a description for a SUSE Linux Enterprise Server 15 SP3
BYOS image for several cloud service provider frameworks.

The parameters `<git-recipes>` and `<git-branch>` may be used multiple times if
the image description should be composed from more than one repository.

The system the source service is run on needs to have `keg` and
`obs-service-keg` installed. Refer to the `Using Source Services
<https://openbuildservice.org/help/manuals/obs-user-guide/cha.obs.source_service.html>`_
section of the OBS manual about details on how to run the source service and
which operating modes are available.