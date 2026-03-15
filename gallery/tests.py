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
        self.assertIn('a href="/kaya/edit"', results.content.decode("utf-8"))

        # Should not see the link on other peopls' pages:
        results = c.get("/kruger")
        self.assertNotIn('a href="/kruger/edit"', results.content.decode("utf-8"))

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
        self.assertIn("your bio here", results.content.decode("utf-8"))

        results = c.post("/accounts/login/", {"username": "kruger",
                                              "password": "stormlord"})
        results = c.post("/kruger/edit",
                         {"bio": "interested in lightning and destroying civilization"})
        self.assertEqual(results.status_code, 302)
        self.assertTrue(results.url.endswith, "/kruger")
        results = c.get("/kruger")
        self.assertEqual(results.status_code, 200)
        self.assertIn("interested in lightning and destroying civilization",
                        results.content.decode("utf-8"))

    
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
        self.assertIn('a href="/kaya/newgallery"', results.content.decode("utf-8"))
        # but not on other peoples':
        results = c.get("/krueger")
        self.assertNotIn('a href="/krueger/newgallery"', results.content.decode("utf-8"))

        # If I load my own I should get a page with a form:
        results = c.get("/kaya/newgallery")
        self.assertEqual(results.status_code, 200)
        self.assertIn('<input type="submit"', results.content.decode("utf-8"))
        # it should not be showing me any error messages:
        self.assertNotIn('This field is required', results.content.decode("utf-8"))

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
        self.assertIn("some pics i took in the desert", results.content.decode("utf-8"))

        
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
        self.assertIn('a href="/kruger/lightning"', results.content.decode("utf-8"))

        
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
        self.assertIn('a href="/kaya/doggies/edit"', results.content.decode("utf-8"))

        # Test my gallery page also has a New Work link
        self.assertIn('a href="/kaya/doggies/new"', results.content.decode("utf-8"))

        # Should not see the link on other peopls' pages:
        results = c.get("/kruger/lightning")
        self.assertEqual(results.status_code, 200)
        self.assertNotIn('a href="/kruger/lightning/edit"', results.content.decode("utf-8"))
        self.assertNotIn('a href="/kruger/lightning/new"', results.content.decode("utf-8"))


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
        self.assertIn("Private Collection", results.content.decode("utf-8"))

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
        self.assertIn("for destroying civilization", results.content.decode("utf-8"))


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
        self.assertIn("<strong>for destroying civilization</strong>", results.content.decode("utf-8"))


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
        self.assertIn("favorite lightning pics", results.content.decode("utf-8"))

        # gallery should no longer exist under old title:
        results = c.get("/kruger/thunder")
        self.assertEqual(results.status_code, 200)
        self.assertIn("No user/gallery/work by that name.", results.content.decode("utf-8"))


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
        self.assertIn("<h2>Menoth</h2>", results.content.decode("utf-8"))
        self.assertIn("First we electrocute all the choir", results.content.decode("utf-8"))
        
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
        self.assertIn("<h2>Menoth</h2>", results.content.decode("utf-8"))
        self.assertIn("First we electrocute all the <strong>choir</strong>",
                        results.content.decode("utf-8")) # markdown shoulda converted ** to <strong>

        # test that page includes edit link, if i'm kruger
        self.assertIn('<a href="/kruger/plans/menoth/edit">', results.content.decode("utf-8"))

        # test that the work page links back to the person and gallery pages
        self.assertIn('<a href="/kruger">', results.content.decode("utf-8"))
        self.assertIn('<a href="/kruger/plans">', results.content.decode("utf-8"))

        # Test that link to new work shows up on the /kruger/plans gallery page
        results = c.get("/kruger/plans")
        self.assertEqual(results.status_code, 200)
        self.assertIn('<a href="/kruger/plans/menoth">Menoth', results.content.decode("utf-8"))

        # There should not be a Next link because this is only work in gallery so far
        self.assertNotIn('Next: ', results.content.decode("utf-8"))
        # Make a second post in gallery:
        results = c.post("/kruger/plans/new", {"workType": "WRI",
                                               "title": "Khador",
                                               "body": "Get those warjacks with my warpwolves!",
                                                "publicity": "PRI"})
        # first work's page should have a next link to the second:
        results = c.get("/kruger/plans/menoth")
        self.assertEqual(results.status_code, 200)
        self.assertIn('<a href="/kruger/plans/khador">Next', results.content.decode("utf-8"))

        # second work's page should have a previous link to the first:
        results = c.get("/kruger/plans/khador")
        self.assertEqual(results.status_code, 200)
        self.assertIn('<a href="/kruger/plans/menoth">Previous', results.content.decode("utf-8"))

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
        self.assertIn("First we electrocute all the **choir**", results.content.decode("utf-8"))
        
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

    def testLoadFunkyUrl(self):
        # TODO test that URL mapper lets us load a page with a hypehn in th ename!!
        pass

        
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
        self.assertIn("<h2>new</h2>", results.content.decode("utf-8"))

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
        self.assertIn("<h2>wolves</h2>", results.content.decode("utf-8"))
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
        self.assertIn("<h2>wolves</h2>", results.content.decode("utf-8"))

    def testBlankTitle(self):
        c = Client()
        self.createBasicUser()
        results = c.post("/accounts/login/", {"username": "kruger",
                                              "password": "stormlord"})
        results = c.post("/kruger/newgallery", {"title": "plans",
                                        "blurb": "**for destroying civilization**",
                                        "publicity": "PRI"})
        # Test that we can submit a blank title and that it gets titled with a
        # number (don't care if title is a number actually just that there's
        # *something* to click on , on the gallery page!)

        results = c.post("/kruger/plans/new", {"workType": "PIC",
                                               "title": "",
                                               "body": "hello",
                                               "publicity": "PRI"})
        self.assertEqual(results.status_code, 302)
        results = c.get("/kruger/plans")
        self.assertEqual(results.status_code, 200)
        # should be a link to "1" in these results:
        self.assertIn('<a href="/kruger/plans/1">1</a>', results.content.decode("utf-8"))
        # in the future the content of this link might be a thumbnail or whatever.


    def testLoadWorkWithDocument(self):
        # not sure how we would test file upload?
        pass
        

# Tests to still write:
# - post new work with and without tags
# - post new work with and without something in the img upload field
#     if something is in the img upload field, then when we view the work, that img should display, whether there's
#     a placeholder for it in work body or not
#     it should also be set as thumbnail.
# - post a new work with no image, then go to edit work, use the inline img form to add an image, then save
#    - should get the img placeholder in the work body
#    - should get association created between document and work
#    - document file should have been uploaded
#    - the first document that's an img should also become the thumbnail
#
# - create a subscriber to a tag
#    - make a new public post with that tag. subscriber should get notified with a plain link.
#    - make a new friends-only post in a public gallery with that tag. subscriber should get
#       notified with a link containing an invite key (Should there be some auth for this???)
#    - make a new post in a friends-only gallery with that tag. subscriber should get notified
#       with a link containing an invite key that works for the gallery.
#    - after loading a page with the invite key, i should also be able to list the gallery and
#       visit any other works in it.
#    - make a new post with no tags, save it.  Then add a tag to it and save it again. Subscribers
#       should get notified as above.
#    - do the above and edit it and save it again. No notifications should go out to subscribers
#       who already got a notification.
#    - Add a new subscriber to that tag.  Save a post that's already gone out to existing
#       subscribers. The new subscriber should still be notified.
#    - Add multiple tags. Subscribers to any of the tags should get notified. Someone who subscribes
#       to all of the tags on the post should still only get notified once.
#
#  - multi-upload some images.
#   - go to the unused img browser. They should all be listed there.
#     - select some and save as "new gallery"
#     - select some and save as "new entries to existing gallery"
#     - select some and save as "new work with all these images"
#   - the new work(s) and/or gallery should be created. Those images should no longer appear
#     as unused images.
#   - the new work should get its "happend_at" field set to the date in the filename of the photo
#
#   - when we add new works to a gallery in this way they should inherit the publicity setting
#     of the gallery.
#   - gallery should sort by the happened_at date
#   - most recently happend_at thumbnail should show on the frontpage
