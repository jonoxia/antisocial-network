from django.test import TestCase
from django.test import Client
from gallery.models import Human, Work

class GalleryTestCase(TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass

    def createBasicUser(self):
        c = Client()
        results = c.post("/accounts/create", {"username": "kruger",
                                             "email": "kruger@circle.org",
                                             "password": "stormlord",
                                             "confirm_password": "stormlord"})
        return results

    
    def testAccountCreation(self):
        results = self.createBasicUser()
        # that should give us a redirect to the edit page
        self.assertEqual(results.status_code, 302)
        self.assertTrue(results.url.endswith("/kruger/edit"))
        # And it should have created a Human object:
        matches = Human.objects.filter(publicName = "kruger")
        self.assertEqual(len(matches), 1)


    def testCannotEditOtherProfiles(self):
        # if i log in as one guy i can't edit another guy's profile
        c = Client()
        self.createBasicUser()
        results = c.post("/accounts/create", {"username": "kaya",
                                             "email": "kaya@circle.org",
                                             "password": "moonhunter",
                                             "confirm_password": "moonhunter"})
        
        
        results = c.post("/accounts/login/", {"username": "kaya",
                                              "password": "moonhunter"})
        # Should see an edit link on my own profile page:
        results = c.get("/kaya")
        self.assertIn('a href="/kaya/edit"', results.content)

        # Should not see the link on other peopls' pages:
        results = c.get("/kruger")
        self.assertNotIn('a href="/kruger/edit"', results.content)

        # If I try to load the edit page directly i should get redirected:
        results = c.get("/kruger/edit")
        self.assertEqual(results.status_code, 302)
        self.assertTrue(results.url.endswith("/kruger"))

        # If I try to load my own though I can go there:
        results = c.get("/kaya/edit")
        self.assertEqual(results.status_code, 200)


    def testEditProfile(self):
        c = Client()
        self.createBasicUser()
        results = c.get("/kruger")
        self.assertEqual(results.status_code, 200)
        self.assertIn("your bio here", results.content)

        results = c.post("/accounts/login/", {"username": "kruger",
                                              "password": "stormlord"})
        results = c.post("/kruger/edit",
                         {"bio": "interested in lightning and destroying civilization"})
        self.assertEqual(results.status_code, 302)
        self.assertTrue(results.url.endswith, "/kruger")
        results = c.get("/kruger")
        self.assertEqual(results.status_code, 200)
        self.assertIn("interested in lightning and destroying civilization",
                        results.content)

    
    def testNewGalleryLink(self):
        # on my profile page I should see link to create new gallery
        c = Client()
        self.createBasicUser()
        results = c.post("/accounts/create", {"username": "kaya",
                                             "email": "kaya@circle.org",
                                             "password": "moonhunter",
                                             "confirm_password": "moonhunter"})

        results = c.post("/accounts/login/", {"username": "kaya",
                                              "password": "moonhunter"})
        # Should see a new gallery link on my own profile page:
        results = c.get("/kaya")
        self.assertIn('a href="/kaya/newgallery"', results.content)
        # but not on other peoples':
        results = c.get("/krueger")
        self.assertNotIn('a href="/krueger/newgallery"', results.content)

        # If I load my own I should get a page with a form:
        results = c.get("/kaya/newgallery")
        self.assertEqual(results.status_code, 200)
        self.assertIn('<input type="submit"', results.content)
        # it should not be showing me any error messages:
        self.assertNotIn('This field is required', results.content)

        # If I load somebody else's i just get redirected:
        results = c.post("/accounts/login/", {"username": "kaya",
                                              "password": "moonhunter"})
        results = c.get("/kruger/newgallery")
        self.assertEqual(results.status_code, 302)
        self.assertTrue(results.url.endswith, "/kruger")
        
    def testCreateGallery(self):
        c = Client()
        self.createBasicUser()
        results = c.post("/accounts/login/", {"username": "kruger",
                                              "password": "stormlord"})

        # should be able to load new gallery page:
        results = c.get("/kruger/newgallery")
        self.assertEqual(results.status_code, 200)
        
        # Think about: spaces in gallery names 
        results = c.post("/kruger/newgallery", {"title": "lightning",
                                      "blurb": "some pics i took in the desert",
                                      "type": "photoset",
                                      "theme": "cloudy",
                                      "publicity": "PUB"})
        self.assertEqual(results.status_code, 302)
        self.assertTrue(results.url.endswith, "/kruger/lightning")

        results = c.get("/kruger/lightning")
        self.assertIn("some pics i took in the desert", results.content)

        
    def testLinksToMyGalleries(self):
        # on my profile page I should see links to all my galleries:
        c = Client()
        self.createBasicUser()
        results = c.post("/accounts/login/", {"username": "kruger",
                                              "password": "stormlord"})
        results = c.post("/kruger/newgallery", {"title": "lightning",
                                      "blurb": "some pics i took in the desert",
                                      "type": "photoset",
                                      "theme": "cloudy",
                                      "publicity": "PUB"})
        results = c.get("/kruger")
        self.assertIn('a href="/kruger/lightning"', results.content)

        
    def testViewMyGallery(self):
        # If it's my gallery, I should see an edit link. If it's not mine,
        # I shouldn't.
        c = Client()
        self.createBasicUser()
        results = c.post("/accounts/create", {"username": "kaya",
                                             "email": "kaya@circle.org",
                                             "password": "moonhunter",
                                             "confirm_password": "moonhunter"})
        
        results = c.post("/accounts/login/", {"username": "kruger",
                                              "password": "stormlord"})
        results = c.post("/kruger/newgallery", {"title": "lightning",
                                      "blurb": "some pics i took in the desert",
                                      "type": "photoset",
                                      "theme": "cloudy",
                                      "publicity": "PUB"})

        results = c.post("/accounts/login/", {"username": "kaya",
                                              "password": "moonhunter"})
        results = c.post("/kaya/newgallery", {"title": "doggies",
                                      "blurb": "my favorite doggies :-)",
                                      "type": "photoset",
                                      "theme": "furry",
                                      "publicity": "PUB"})
        # My gallery:
        results = c.get("/kaya/doggies")
        self.assertEqual(results.status_code, 200)
        self.assertIn('a href="/kaya/doggies/edit"', results.content)

        # Test my gallery page also has a New Work link
        self.assertIn('a href="/kaya/doggies/new"', results.content)

        # Should not see the link on other peopls' pages:
        results = c.get("/kruger/lightning")
        self.assertEqual(results.status_code, 200)
        self.assertNotIn('a href="/kruger/lightning/edit"', results.content)
        self.assertNotIn('a href="/kruger/lightning/new"', results.content)


    def testPrivateGallery(self):
        # If gallery is set to private, i should be able to see it, but nobody else.
        c = Client()
        self.createBasicUser()
        results = c.post("/accounts/create", {"username": "kaya",
                                             "email": "kaya@circle.org",
                                             "password": "moonhunter",
                                             "confirm_password": "moonhunter"})
        
        results = c.post("/accounts/login/", {"username": "kruger",
                                              "password": "stormlord"})
        results = c.post("/kruger/newgallery", {"title": "plans",
                                        "blurb": "for destroying civilization",
                                        "publicity": "PRI"})

        # I should be able to see the gallery (with a note that it's private)
        results = c.get("/kruger/plans")
        self.assertEqual(results.status_code, 200)
        self.assertIn("Private Collection", results.content)

        # but kaya shouldn't, she should be redirected:
        results = c.post("/accounts/login/", {"username": "kaya",
                                              "password": "moonhunter"})
        results = c.get("/kruger/plans")
        self.assertEqual(results.status_code, 302)
        self.assertTrue(results.url.endswith, "/kruger")


    def testChangeGalleryPublicity(self):

        c = Client()
        self.createBasicUser()
        results = c.post("/accounts/create", {"username": "kaya",
                                             "email": "kaya@circle.org",
                                             "password": "moonhunter",
                                             "confirm_password": "moonhunter"})

        # Krueger makes private gallery:        
        results = c.post("/accounts/login/", {"username": "kruger",
                                              "password": "stormlord"})
        results = c.post("/kruger/newgallery", {"title": "plans",
                                        "blurb": "for destroying civilization",
                                        "publicity": "PRI"})

        # Kaya tries to view it, can't:
        results = c.post("/accounts/login/", {"username": "kaya",
                                              "password": "moonhunter"})
        results = c.get("/kruger/plans")
        self.assertEqual(results.status_code, 302)
        self.assertTrue(results.url.endswith, "/kruger")

        # Krueger makes it public:
        results = c.post("/accounts/login/", {"username": "kruger",
                                              "password": "stormlord"})
        results = c.post("/kruger/plans/edit", {"publicity": "PUB"})
        self.assertEqual(results.status_code, 302)
        self.assertTrue(results.url.endswith, "/kruger/plans")

        # kaya tries again, can view:
        results = c.post("/accounts/login/", {"username": "kaya",
                                              "password": "moonhunter"})
        results = c.get("/kruger/plans")
        self.assertEqual(results.status_code, 200)
        self.assertIn("for destroying civilization", results.content)


    def testGalleryUsesMarkdown(self):
        c = Client()
        self.createBasicUser()

        results = c.post("/accounts/login/", {"username": "kruger",
                                              "password": "stormlord"})
        results = c.post("/kruger/newgallery", {"title": "plans",
                                        "blurb": "**for destroying civilization**",
                                        "publicity": "PRI"})
        results = c.get("/kruger/plans")
        self.assertEqual(results.status_code, 200)
        self.assertIn("<strong>for destroying civilization</strong>", results.content)


    def testChangeGalleryName(self):
        c = Client()
        self.createBasicUser()

        results = c.post("/accounts/login/", {"username": "kruger",
                                              "password": "stormlord"})
        results = c.post("/kruger/newgallery", {"title": "thunder",
                                        "blurb": "favorite lightning pics",
                                        "publicity": "PRI"})
        # oops i meant to put lightning not thunder
        results = c.post("/kruger/thunder/edit", {"title": "lightning"})

        results = c.get("/kruger/lightning")
        self.assertEqual(results.status_code, 200)
        self.assertIn("favorite lightning pics", results.content)

        # gallery should no longer exist under old title:
        results = c.get("/kruger/thunder")
        self.assertEqual(results.status_code, 200)
        self.assertIn("No user/gallery/work by that name.", results.content)


    def testAddWorkToGallery(self):
        c = Client()
        self.createBasicUser()
        results = c.post("/accounts/login/", {"username": "kruger",
                                              "password": "stormlord"})
        results = c.post("/kruger/newgallery", {"title": "plans",
                                        "blurb": "**for destroying civilization**",
                                        "publicity": "PRI"})
        # work type is a text field so we can put whatever we want there
        # let's do a text post for now, uploading images comes later
        results = c.post("/kruger/plans/new", {"workType": "WRI",
                                               "title": "Menoth",
                                               "body": "First we electrocute all the choir",
                                               "publicity": "PRI"})
        # work object should have been created:
        matches = Work.objects.filter(gallery__title = "plans")
        self.assertEqual(matches.count(), 1)
        self.assertEqual(matches[0].title, "Menoth")
        self.assertEqual(matches[0].body, "First we electrocute all the choir")
        self.assertEqual(matches[0].sequenceNum, 1)

        self.assertEqual(results.status_code, 302)
        # We should be redirected to the page /kruger/plans/Menoth
        self.assertTrue(results.url.endswith, "/kruger/plans/menoth")
        # Test that /kruger/plans/Menoth renders a page with the right title/body
        results = c.get("/kruger/plans/menoth")
        self.assertEqual(results.status_code, 200)
        self.assertIn("<h2>Menoth</h2>", results.content)
        self.assertIn("First we electrocute all the choir", results.content)
        
        # TODO test that i can't create a work in someone else's gallery
        
        # Test that if we add several works, their sequence nums are sequential:
        results = c.post("/kruger/plans/new", {"workType": "WRI",
                                               "title": "Khador",
                                               "body": "Get those warjacks with my warpwolves!",
                                                "publicity": "PRI"})
        matches = Work.objects.filter(gallery__title = "plans")
        self.assertEqual(matches.count(), 2)
        matches = Work.objects.filter(title = "Khador", gallery__title = "plans")
        self.assertEqual(matches.count(), 1)
        self.assertEqual(matches[0].title, "Khador")
        self.assertEqual(matches[0].body, "Get those warjacks with my warpwolves!")
        self.assertEqual(matches[0].sequenceNum, 2)


    def testWorkPage(self):
        c = Client()
        self.createBasicUser()
        results = c.post("/accounts/login/", {"username": "kruger",
                                              "password": "stormlord"})
        results = c.post("/kruger/newgallery", {"title": "plans",
                                        "blurb": "**for destroying civilization**",
                                        "publicity": "PRI"})
        results = c.post("/kruger/plans/new", {"workType": "WRI",
                                               "title": "Menoth",
                                               "body": "First we electrocute all the **choir**",
                                                "publicity": "PRI"})

        results = c.get("/kruger/plans/menoth")
        self.assertEqual(results.status_code, 200)
        self.assertIn("<h2>Menoth</h2>", results.content)
        self.assertIn("First we electrocute all the <strong>choir</strong>",
                        results.content) # markdown shoulda converted ** to <strong>

        # test that page includes edit link, if i'm kruger
        self.assertIn('<a href="/kruger/plans/menoth/edit">', results.content)

        # test that the work page links back to the person and gallery pages
        self.assertIn('<a href="/kruger">', results.content)
        self.assertIn('<a href="/kruger/plans">', results.content)

        # Test that link to new work shows up on the /kruger/plans gallery page
        results = c.get("/kruger/plans")
        self.assertEqual(results.status_code, 200)
        self.assertIn('<a href="/kruger/plans/menoth">Menoth', results.content)

        # There should not be a Next link because this is only work in gallery so far
        self.assertNotIn('Next: ', results.content)
        # Make a second post in gallery:
        results = c.post("/kruger/plans/new", {"workType": "WRI",
                                               "title": "Khador",
                                               "body": "Get those warjacks with my warpwolves!",
                                                "publicity": "PRI"})
        # first work's page should have a next link to the second:
        results = c.get("/kruger/plans/menoth")
        self.assertEqual(results.status_code, 200)
        self.assertIn('<a href="/kruger/plans/khador">Next', results.content)

        # second work's page should have a previous link to the first:
        results = c.get("/kruger/plans/khador")
        self.assertEqual(results.status_code, 200)
        self.assertIn('<a href="/kruger/plans/menoth">Previous', results.content)

        # TODO test that default state of work is private until I publish it


    def testEditWork(self):
        # First make a work:
        c = Client()
        self.createBasicUser()
        results = c.post("/accounts/login/", {"username": "kruger",
                                              "password": "stormlord"})
        results = c.post("/kruger/newgallery", {"title": "plans",
                                        "blurb": "**for destroying civilization**",
                                        "publicity": "PRI"})
        results = c.post("/kruger/plans/new", {"workType": "WRI",
                                               "title": "Menoth",
                                               "body": "First we electrocute all the **choir**",
                                               "publicity": "PRI"})

        # Look at the edit page for it. Markdown should be displayed (literally)
        # inside a text field:
        results = c.get("/kruger/plans/menoth/edit")
        self.assertEqual(results.status_code, 200)
        self.assertIn("First we electrocute all the **choir**", results.content)
        
        # Test changing publicity:
        matches = Work.objects.filter(gallery__title = "plans")
        self.assertEqual(matches.count(), 1)
        self.assertEqual(matches[0].publicity, "PRI")
        results = c.post("/kruger/plans/menoth/edit", {"title": "Menoth",
                                                        "body": "First we electrocute all the **choir**",
                                                        "publicity": "PUB"})
        self.assertEqual(results.status_code, 302)
        self.assertTrue(results.url.endswith, "/kruger/plans/menoth")
        matches = Work.objects.filter(gallery__title = "plans")
        self.assertEqual(matches.count(), 1)
        self.assertEqual(matches[0].publicity, "PUB")

        
        # Test changing body text
        results = c.post("/kruger/plans/menoth/edit", {"title": "Menoth",
                                                        "body": "First we electrocute all the **zealots**",
                                                        "publicity": "PUB"})
        self.assertEqual(results.status_code, 302)
        self.assertTrue(results.url.endswith, "/kruger/plans/menoth")
        matches = Work.objects.filter(gallery__title = "plans")
        self.assertEqual(matches.count(), 1)
        self.assertEqual(matches[0].body, "First we electrocute all the **zealots**")

        # TODO test changing title (with a check that you're not duplicating
        # a name in the same gallery)

    def testMakeUrlName(self):
        from gallery.views import make_url_name
        self.assertEqual(make_url_name("foo1 bar2 baz3", []),
                         "foo1-bar2-baz3") # replace spaces, preserve numbers
        self.assertEqual(make_url_name("Alice's Restaurant", []),
                         "alices-restaurant") # drop punctuation, lowercase
        self.assertEqual(make_url_name("Alice's Restaurant", ["alices-restaurant"]),
                         "alices-restaurant_1") # make all unique

        self.assertEqual(make_url_name("edit", []),
                         "edit_1") # don't use reserved word

        self.assertEqual(make_url_name("edit", ["edit_1"]),
                         "edit_2") # don't use alrady-used euphemism for reserved word

        self.assertEqual(make_url_name("", [""]),
                         "_1") # Give me numbers for blanks
                         
        self.assertEqual(make_url_name("", ["_1"]),
                         "_2") # Increment the numbers
                         

        
    def testWorksGetUniqueUrlNames(self):
        c = Client()
        self.createBasicUser()
        results = c.post("/accounts/login/", {"username": "kruger",
                                              "password": "stormlord"})
        results = c.post("/kruger/newgallery", {"title": "plans",
                                        "blurb": "**for destroying civilization**",
                                        "publicity": "PRI"})

        # If we try to name a title after a reserved word it should be renamed
        results = c.post("/kruger/plans/new", {"workType": "WRI",
                                               "title": "new",
                                               "body": "hello",
                                               "publicity": "PRI"})
        # work object should have been created:
        matches = Work.objects.filter(gallery__title = "plans")
        self.assertEqual(matches.count(), 1)
        self.assertEqual(matches[0].title, "new")
        self.assertEqual(matches[0].urlname, "new_1")
        self.assertEqual(results.status_code, 302)
        self.assertTrue(results.url.endswith, "/kruger/plans/new_1")
        results = c.get("/kruger/plans/new_1")
        self.assertEqual(results.status_code, 200)
        self.assertIn("<h2>new</h2>", results.content)

        # If we try to make two works with same title in same gallery, the second
        # one should get a suffix to make both URLs unique, but titles should not
        # be changed.
        results = c.post("/kruger/plans/new", {"workType": "WRI",
                                               "title": "wolves",
                                               "body": "hello",
                                               "publicity": "PRI"})
        matches = Work.objects.filter(gallery__title = "plans",
                                      title = "wolves")
        self.assertEqual(matches.count(), 1)
        self.assertEqual(matches[0].urlname, "wolves")
        self.assertEqual(results.status_code, 302)
        self.assertTrue(results.url.endswith, "/kruger/plans/wolves")
        results = c.get("/kruger/plans/wolves")
        self.assertEqual(results.status_code, 200)
        self.assertIn("<h2>wolves</h2>", results.content)
        results = c.post("/kruger/plans/new", {"workType": "WRI",
                                               "title": "wolves",
                                               "body": "hello",
                                               "publicity": "PRI"})
        matches = Work.objects.filter(gallery__title = "plans",
                                      title = "wolves")
        self.assertEqual(matches.count(), 2)
        self.assertEqual(matches[0].urlname, "wolves")
        self.assertEqual(matches[1].urlname, "wolves_1")
        self.assertEqual(results.status_code, 302)
        self.assertTrue(results.url.endswith, "/kruger/plans/wolves_1")
        results = c.get("/kruger/plans/wolves_1")
        self.assertEqual(results.status_code, 200)
        self.assertIn("<h2>wolves</h2>", results.content)
        
        

                # What do we post when adding a new work to a gallery?
        # is it ready for publication or is it a draft?
        # can I upload arbitrary files? like a PDF or word document?
        # need to know what gallery it's part of (URL tells us this)
        # What is the type?
        #  type 1: simple picture with optional caption
        #            (can i replace the picture while editing? or not?)
        #  type 2: blog post: a lot of text in markdown, with optional pictures
        #            interspersed
        #  (note type 2 is a superset of type 1 -- they could be stored the same
        #    way but the UI for creating and viewing them might be different)
        #  type 3: audio file:
        #  type 4: quick link: an external URL with a caption or content
        #  type 5: interactive (i.e. custom javascript files e.g. a game)

        # future features:  Move a work to another gallery
        #   share a work between multiple galleries?
        #       i.e. this goes in my "all my writings" gallery as well as my
        #       "all my complaints about computers" gallery
        #   share a work between multiple humans?
        #   edit a work
        #   publish a work (public or friends-only)
        #   see all my drafts
        #   choose gallery style
        #   choose gallery display order (chronological vs. alphabetical by title vs.
        #    custom order vs. something else?)


        # MINIMAL FEATURES for me to start using this website as a website:
        # new work, edit work, style the gallery page, style the work page
