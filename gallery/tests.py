from django.test import TestCase
from django.test import Client
from gallery.models import Human

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
                                      "public": True})
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
                                      "public": True})
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
                                      "public": True})

        results = c.post("/accounts/login/", {"username": "kaya",
                                              "password": "moonhunter"})
        results = c.post("/kaya/newgallery", {"title": "doggies",
                                      "blurb": "my favorite doggies :-)",
                                      "type": "photoset",
                                      "theme": "furry",
                                      "public": True})
        # My gallery:
        results = c.get("/kaya/doggies")
        self.assertEqual(results.status_code, 200)
        self.assertIn('a href="/kaya/doggies/edit"', results.content)
        
        # Should not see the link on other peopls' pages:
        results = c.get("/kruger/lightning")
        self.assertEqual(results.status_code, 200)
        self.assertNotIn('a href="/kruger/lightning/edit"', results.content)
