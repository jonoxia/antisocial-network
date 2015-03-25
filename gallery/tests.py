from django.test import TestCase
from django.test import Client
from gallery.models import Human

# Create your tests here.
class GalleryTestCase(TestCase):
    def setUp(self):
        pass
    
    def tearDown(self):
        pass

    def testAccountCreation(self):
        c = Client()
        results = c.post("/accounts/create", {"username": "kruger",
                                             "email": "kruger@circle.org",
                                             "password": "stormlord",
                                             "confirm_password": "stormlord"})
        # that should give us a redirect to the edit page
        self.assertEqual(results.status_code, 302)
        self.assertTrue(results.url.endswith("/kruger/edit"))
        # And it should have created a Human object:
        matches = Human.objects.filter(publicName = "kruger")
        self.assertEqual(len(matches), 1)
        


    def testCannotEditOtherProfiles(self):
        # if i log in as one guy i can't edit another guy's profile
        c = Client()
        results = c.post("/accounts/create", {"username": "kruger",
                                             "email": "kruger@circle.org",
                                             "password": "stormlord",
                                             "confirm_password": "stormlord"})
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
